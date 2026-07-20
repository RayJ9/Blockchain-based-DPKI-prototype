param(
  [int]$MeanBlockMs = 200,
  [UInt32]$DifficultyBits = 521142271,
  [switch]$Build,
  [switch]$Clean,
  [int]$RpcBase = 8545,
  [int]$JrpcBase = 8801,
  [int]$GrpcBase = 8802,
  [int]$WsBase = 8546,
  [int]$HealthBase = 8805,
  [int]$P2pBase = 13803,
  [int]$WarmupSeconds = 65,
  [switch]$MineEmpty,
  [switch]$AggregateMiningOnNode0
)

$ErrorActionPreference = "Stop"

$PowRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DpkiRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$WorkspaceRoot = $DpkiRoot
$PluginRoot = Join-Path $WorkspaceRoot "omnilink\omnilink-plugin"
$TemplateConfig = Join-Path $PluginRoot "omnilink.pow.toml"
$Exe = Join-Path $PluginRoot "build\omni.exe"
$RuntimeRoot = Join-Path $PowRoot "runtime"
$ConfigDir = Join-Path $RuntimeRoot "configs"
$LogDir = Join-Path $RuntimeRoot "logs"
$ReadyFile = Join-Path $RuntimeRoot "ready.txt"
$NodeCount = 4

function Assert-UnderPath {
  param([string]$Child, [string]$Parent)
  $childFull = [System.IO.Path]::GetFullPath($Child)
  $parentFull = [System.IO.Path]::GetFullPath($Parent)
  if (-not $childFull.StartsWith($parentFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to operate outside $parentFull`: $childFull"
  }
}

function Test-ProcessAlive {
  param([int]$PidValue)
  return [bool](Get-Process -Id $PidValue -ErrorAction SilentlyContinue)
}

function Test-PortInUse {
  param([int]$Port)
  return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Web3Rpc {
  param([string]$Url, [int]$TimeoutSeconds = 90)
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $body = @{ jsonrpc = "2.0"; id = 1; method = "net_listening"; params = @() } | ConvertTo-Json -Compress
  while ((Get-Date) -lt $deadline) {
    try {
      $reply = Invoke-RestMethod -Uri $Url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 2
      if ($reply.result -eq $true) {
        return
      }
    } catch {
      Start-Sleep -Milliseconds 500
      continue
    }
    Start-Sleep -Milliseconds 500
  }
  throw "Web3 RPC did not become ready at $Url"
}

function Wait-Web3PowReady {
  param([string]$Url, [int]$TimeoutSeconds = 150)
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $blockBody = @{ jsonrpc = "2.0"; id = 1; method = "eth_blockNumber"; params = @() } | ConvertTo-Json -Compress
  while ((Get-Date) -lt $deadline) {
    try {
      $blockReply = Invoke-RestMethod -Uri $Url -Method Post -Body $blockBody -ContentType "application/json" -TimeoutSec 2
      $hex = [string]$blockReply.result
      if ($hex.StartsWith("0x")) {
        $blockNumber = [Convert]::ToInt64($hex.Substring(2), 16)
      } else {
        $blockNumber = [int64]$hex
      }
      if ($blockNumber -gt 0) {
        return
      }
    } catch {
      Start-Sleep -Milliseconds 500
      continue
    }
    Start-Sleep -Milliseconds 500
  }
  throw "Web3 RPC became reachable but PoW chain did not become ready at $Url"
}

function Set-TomlValue {
  param([string]$Text, [string]$Pattern, [string]$Replacement)
  return [regex]::Replace($Text, $Pattern, $Replacement, [System.Text.RegularExpressions.RegexOptions]::Multiline)
}

if ($Build -or -not (Test-Path $Exe)) {
  & (Join-Path $PSScriptRoot "build-omnilink-pow.ps1")
}

if (-not (Test-Path $Exe)) {
  throw "Omnilink binary not found at $Exe"
}

if ($Clean -and (Test-Path $RuntimeRoot)) {
  & (Join-Path $PSScriptRoot "stop-omnilink-pow-4nodes.ps1")
  Assert-UnderPath $RuntimeRoot $PowRoot
  $removed = $false
  for ($attempt = 1; $attempt -le 10; $attempt += 1) {
    try {
      Remove-Item -LiteralPath $RuntimeRoot -Recurse -Force
      $removed = $true
      break
    } catch {
      if ($attempt -eq 10) {
        throw
      }
      Start-Sleep -Milliseconds 500
    }
  }
  if (-not $removed) {
    throw "Failed to clean $RuntimeRoot"
  }
}

New-Item -ItemType Directory -Force -Path $RuntimeRoot, $ConfigDir, $LogDir | Out-Null

$running = @()
for ($i = 0; $i -lt $NodeCount; $i += 1) {
  $pidFile = Join-Path $RuntimeRoot "node$i.pid"
  if (Test-Path $pidFile) {
    $pidValue = [int](Get-Content $pidFile)
    if (Test-ProcessAlive $pidValue) {
      $running += "node$i(pid=$pidValue)"
    }
  }
}
if ($running.Count -gt 0) {
  throw "Omnilink PoW nodes already running: $($running -join ', '). Run stop-omnilink-pow-4nodes.ps1 first."
}

$ports = @()
for ($i = 0; $i -lt $NodeCount; $i += 1) {
  $ports += ($RpcBase + $i * 10)
  $ports += ($JrpcBase + $i * 10)
  $ports += ($GrpcBase + $i * 10)
  $ports += ($WsBase + $i * 10)
  $ports += ($HealthBase + $i * 10)
  $ports += ($P2pBase + $i)
}
foreach ($port in $ports) {
  if (Test-PortInUse $port) {
    throw "Port $port is already in use. Stop the existing node or choose another base port."
  }
}

$template = Get-Content -LiteralPath $TemplateConfig -Raw
$mineEmptyValue = if ($MineEmpty) { "true" } else { "false" }
$allPids = @()
for ($i = 0; $i -lt $NodeCount; $i += 1) {
  $nodeDir = Join-Path $RuntimeRoot "node$i"
  $configPath = Join-Path $ConfigDir "node$i.toml"
  $stdout = Join-Path $LogDir "node$i.stdout.log"
  $stderr = Join-Path $LogDir "node$i.stderr.log"
  $pidFile = Join-Path $RuntimeRoot "node$i.pid"
  $jrpc = $JrpcBase + $i * 10
  $grpc = $GrpcBase + $i * 10
  $http = $RpcBase + $i * 10
  $ws = $WsBase + $i * 10
  $health = $HealthBase + $i * 10
  $p2p = $P2pBase + $i
  $grpcLog = (Join-Path $LogDir "grpc33-node$i.log").Replace("\", "/")
  $nodeLocalMiners = 1
  $disableMiningValue = "false"
  if ($AggregateMiningOnNode0) {
    if ($i -eq 0) {
      $nodeLocalMiners = $NodeCount
    } else {
      $nodeLocalMiners = 0
      $disableMiningValue = "true"
    }
  }

  New-Item -ItemType Directory -Force -Path $nodeDir | Out-Null

  $config = $template
  $config = Set-TomlValue $config 'singleMode\s*=\s*(true|false)' 'singleMode=false'
  $config = Set-TomlValue $config 'grpcLogFile\s*=\s*"[^"]+"' "grpcLogFile=`"$grpcLog`""
  $config = Set-TomlValue $config '^port\s*=\s*\d+' "port=$p2p"
  $config = Set-TomlValue $config 'jrpcBindAddr\s*=\s*"[^"]+"' "jrpcBindAddr=`"localhost:$jrpc`""
  $config = Set-TomlValue $config 'grpcBindAddr\s*=\s*"[^"]+"' "grpcBindAddr=`"localhost:$grpc`""
  $config = Set-TomlValue $config 'httpAddr\s*=\s*"[^"]+"' "httpAddr=`"localhost:$http`""
  $config = Set-TomlValue $config 'wsAddr\s*=\s*"[^"]+"' "wsAddr=`"localhost:$ws`""
  $config = Set-TomlValue $config 'listenAddr\s*=\s*"[^"]+"' "listenAddr=`"localhost:$health`""
  $config = Set-TomlValue $config 'maintainers\s*=\s*\d+' "maintainers=$NodeCount"
  $config = Set-TomlValue $config 'localMiners\s*=\s*\d+' "localMiners=$nodeLocalMiners"
  $config = Set-TomlValue $config 'minerId\s*=\s*\d+' "minerId=$i"
  $config = Set-TomlValue $config 'meanBlockMs\s*=\s*\d+' "meanBlockMs=$MeanBlockMs"
  $config = Set-TomlValue $config 'difficultyBits\s*=\s*\d+' "difficultyBits=$DifficultyBits"
  $config = Set-TomlValue $config 'mineEmpty\s*=\s*(true|false)' "mineEmpty=$mineEmptyValue"
  $config = Set-TomlValue $config 'disableMining\s*=\s*(true|false)' "disableMining=$disableMiningValue"
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($configPath, $config, $utf8NoBom)

  $argList = "-f `"$configPath`" -datadir `"$nodeDir`""
  $process = Start-Process `
    -FilePath $Exe `
    -ArgumentList $argList `
    -WorkingDirectory $PluginRoot `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -WindowStyle Hidden `
    -PassThru
  $process.Id | Set-Content -LiteralPath $pidFile
  $allPids += $process.Id
  Write-Host "Started node$i PID $($process.Id): web3=http://127.0.0.1:$http jrpc=http://127.0.0.1:$jrpc p2p=$p2p"
}

Start-Sleep -Seconds 2
for ($i = 0; $i -lt $NodeCount; $i += 1) {
  $pidValue = [int](Get-Content (Join-Path $RuntimeRoot "node$i.pid"))
  if (-not (Test-ProcessAlive $pidValue)) {
    throw "node$i exited during startup. Check $LogDir\node$i.stderr.log and node$i.stdout.log"
  }
}

Wait-Web3Rpc "http://127.0.0.1:$RpcBase"
if ($MineEmpty) {
  Wait-Web3PowReady "http://127.0.0.1:$RpcBase"
} else {
  Start-Sleep -Seconds $WarmupSeconds
}

($allPids -join "`n") | Set-Content -LiteralPath (Join-Path $RuntimeRoot "omnilink-pow-4nodes.pids")
Get-Date -Format o | Set-Content -LiteralPath $ReadyFile
Write-Host "Omnilink PoW 4-node network is ready."
Write-Host "Aggregate target block interval: ${MeanBlockMs} ms"
if ($AggregateMiningOnNode0) {
  Write-Host "Aggregate mining mode: node0 runs $NodeCount local virtual miners; node1-node3 validate/sync without mining."
}
Write-Host "Web3 RPC for DPKI: http://127.0.0.1:$RpcBase"
Write-Host "Runtime: $RuntimeRoot"
