param(
    [int]$MeanBlockMs = 80,
    [UInt32]$DifficultyBits = 521142271,
    [switch]$Build,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$ChainRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BlockchainRoot = Resolve-Path (Join-Path $ChainRoot "..")
$WorkspaceRoot = Resolve-Path (Join-Path $BlockchainRoot "..")
$PluginRoot = Join-Path $WorkspaceRoot "omnilink\omnilink-plugin"
$TemplateConfig = Join-Path $PluginRoot "omnilink.pow.toml"
$Exe = Join-Path $PluginRoot "build\omni.exe"
$RuntimeRoot = Join-Path $ChainRoot "runtime"
$ConfigDir = Join-Path $RuntimeRoot "configs"
$LogDir = Join-Path $RuntimeRoot "logs"

$chains = @(
    [pscustomobject]@{ Name = "main";  ChainId = 4100; Rpc = 18645; Jrpc = 18801; Grpc = 18802; Ws = 18646; Health = 18805; P2p = 19803 },
    [pscustomobject]@{ Name = "side-a"; ChainId = 4101; Rpc = 18745; Jrpc = 18901; Grpc = 18902; Ws = 18746; Health = 18905; P2p = 19903 },
    [pscustomobject]@{ Name = "side-b"; ChainId = 4102; Rpc = 18845; Jrpc = 19001; Grpc = 19002; Ws = 18846; Health = 19005; P2p = 20003 }
)

function Set-TomlValue {
    param([string]$Text, [string]$Pattern, [string]$Replacement)
    return [regex]::Replace($Text, $Pattern, $Replacement, [System.Text.RegularExpressions.RegexOptions]::Multiline)
}

function Wait-Web3Ready {
    param([string]$Url, [int]$TimeoutSeconds = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $body = @{ jsonrpc = "2.0"; id = 1; method = "eth_blockNumber"; params = @() } | ConvertTo-Json -Compress
    while ((Get-Date) -lt $deadline) {
        try {
            $reply = Invoke-RestMethod -Uri $Url -Method Post -Body $body -ContentType "application/json" -TimeoutSec 2
            if ([string]$reply.result -match '^0x[0-9a-fA-F]+$') {
                return
            }
        } catch {
        }
        Start-Sleep -Milliseconds 500
    }
    throw "Chain RPC did not become ready at $Url"
}

if ($Build -or -not (Test-Path -LiteralPath $Exe)) {
    & (Join-Path $BlockchainRoot "pow-4nodes-runtime\scripts\build-omnilink-pow.ps1")
}
if (-not (Test-Path -LiteralPath $Exe)) {
    throw "Omnilink binary not found at $Exe"
}

if ($Clean) {
    & (Join-Path $PSScriptRoot "stop-three-chains.ps1")
    if (Test-Path -LiteralPath $RuntimeRoot) {
        $resolvedRuntime = [System.IO.Path]::GetFullPath($RuntimeRoot)
        $resolvedChainRoot = [System.IO.Path]::GetFullPath($ChainRoot)
        if (-not $resolvedRuntime.StartsWith($resolvedChainRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean runtime outside $resolvedChainRoot"
        }
        Remove-Item -LiteralPath $RuntimeRoot -Recurse -Force
    }
}

New-Item -ItemType Directory -Force -Path $RuntimeRoot, $ConfigDir, $LogDir | Out-Null

foreach ($chain in $chains) {
    foreach ($port in @($chain.Rpc, $chain.Jrpc, $chain.Grpc, $chain.Ws, $chain.Health, $chain.P2p)) {
        if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
            throw "Port $port is already in use."
        }
    }
}

$template = Get-Content -LiteralPath $TemplateConfig -Raw -Encoding UTF8
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$manifest = @()

foreach ($chain in $chains) {
    $name = $chain.Name
    $nodeDir = Join-Path $RuntimeRoot $name
    $configPath = Join-Path $ConfigDir "$name.toml"
    $stdout = Join-Path $LogDir "$name.stdout.log"
    $stderr = Join-Path $LogDir "$name.stderr.log"
    $nodeLog = (Join-Path $LogDir "$name.omnilink.log").Replace("\", "/")
    $grpcLog = (Join-Path $LogDir "$name.grpc.log").Replace("\", "/")
    New-Item -ItemType Directory -Force -Path $nodeDir | Out-Null

    $config = $template
    $config = Set-TomlValue $config '^Title\s*=\s*"[^"]+"' "Title=`"omnilink-$name`""
    $config = Set-TomlValue $config '^evmChainID\s*=\s*\d+' "evmChainID=$($chain.ChainId)"
    # The upstream template carries logFile on a malformed commented line. Make it
    # explicit before -datadir rewrites relative runtime paths.
    $config = Set-TomlValue $config '^#.*?logFile\s*=\s*"[^"]+"' "logFile=`"$nodeLog`""
    $config = Set-TomlValue $config '^logFile\s*=\s*"[^"]+"' "logFile=`"$nodeLog`""
    $config = Set-TomlValue $config '^singleMode\s*=\s*(true|false)' 'singleMode=true'
    $config = Set-TomlValue $config '^grpcLogFile\s*=\s*"[^"]+"' "grpcLogFile=`"$grpcLog`""
    $config = Set-TomlValue $config '^port\s*=\s*\d+' "port=$($chain.P2p)"
    $config = Set-TomlValue $config '^jrpcBindAddr\s*=\s*"[^"]+"' "jrpcBindAddr=`"localhost:$($chain.Jrpc)`""
    $config = Set-TomlValue $config '^grpcBindAddr\s*=\s*"[^"]+"' "grpcBindAddr=`"localhost:$($chain.Grpc)`""
    $config = Set-TomlValue $config '^httpAddr\s*=\s*"[^"]+"' "httpAddr=`"localhost:$($chain.Rpc)`""
    $config = Set-TomlValue $config '^wsAddr\s*=\s*"[^"]+"' "wsAddr=`"localhost:$($chain.Ws)`""
    $config = Set-TomlValue $config '^listenAddr\s*=\s*"[^"]+"' "listenAddr=`"localhost:$($chain.Health)`""
    $config = Set-TomlValue $config '^maintainers\s*=\s*\d+' 'maintainers=1'
    $config = Set-TomlValue $config '^localMiners\s*=\s*\d+' 'localMiners=1'
    $config = Set-TomlValue $config '^minerId\s*=\s*\d+' 'minerId=0'
    $config = Set-TomlValue $config '^meanBlockMs\s*=\s*\d+' "meanBlockMs=$MeanBlockMs"
    $config = Set-TomlValue $config '^difficultyBits\s*=\s*\d+' "difficultyBits=$DifficultyBits"
    $config = Set-TomlValue $config '^mineEmpty\s*=\s*(true|false)' 'mineEmpty=true'
    $config = Set-TomlValue $config '^disableMining\s*=\s*(true|false)' 'disableMining=false'
    [System.IO.File]::WriteAllText($configPath, $config, $utf8NoBom)

    $argList = "-f `"$configPath`" -datadir `"$nodeDir`""
    $process = Start-Process -FilePath $Exe -ArgumentList $argList -WorkingDirectory $PluginRoot `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
    $process.Id | Set-Content -LiteralPath (Join-Path $RuntimeRoot "$name.pid")
    $manifest += [pscustomobject]@{
        name = $name
        chainId = $chain.ChainId
        rpc = "http://127.0.0.1:$($chain.Rpc)"
        jrpc = "http://127.0.0.1:$($chain.Jrpc)"
        p2pPort = $chain.P2p
        pid = $process.Id
    }
    Write-Host "Started $name chain PID $($process.Id): chainId=$($chain.ChainId) rpc=http://127.0.0.1:$($chain.Rpc)"
}

Start-Sleep -Seconds 2
foreach ($chain in $chains) {
    Wait-Web3Ready "http://127.0.0.1:$($chain.Rpc)"
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $RuntimeRoot "chains.json") -Encoding UTF8
Write-Host "Three independent Omnilink chains are ready. Runtime: $RuntimeRoot"
