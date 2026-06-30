param(
    [int]$Maintainers = 4,
    [string]$DataDir = "",
    [switch]$NoBootstrap
)

$ErrorActionPreference = "Stop"

$PackageRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$ProjectRoot = (Resolve-Path (Split-Path -Parent $PackageRoot)).Path
$Omni = (Resolve-Path (Join-Path $ProjectRoot "bin\omni.exe")).Path
$Config = (Resolve-Path (Join-Path $PackageRoot "config\ticket-evm-fast.toml")).Path
$Monitor = (Resolve-Path (Join-Path $PackageRoot "scripts\bootstrap-and-monitor.js")).Path
$LogDir = Join-Path $PackageRoot "logs"
$PidFile = Join-Path $PackageRoot "runtime\ticket-evm-fast.pid"

if ([string]::IsNullOrWhiteSpace($DataDir)) {
    $DataDir = Join-Path $PackageRoot "runtime\ticket-evm-node"
}

New-Item -ItemType Directory -Force $DataDir | Out-Null
New-Item -ItemType Directory -Force (Split-Path -Parent $PidFile) | Out-Null
New-Item -ItemType Directory -Force $LogDir | Out-Null

if (Test-Path $PidFile) {
    $OldPid = Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($OldPid -and (Get-Process -Id $OldPid -ErrorAction SilentlyContinue)) {
        Write-Host "Chain33 ticket+EVM node is already running with PID $OldPid."
        Write-Host "Web3 RPC: http://127.0.0.1:8545"
        Write-Host "Chain33 JSON-RPC: http://127.0.0.1:8801"
        exit 0
    }
}

foreach ($Port in 8545, 8801, 8802) {
    if (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue) {
        throw "Port $Port is already in use. Stop the old Chain33 node first."
    }
}

$Stdout = Join-Path $LogDir "ticket-evm-fast.stdout.log"
$Stderr = Join-Path $LogDir "ticket-evm-fast.stderr.log"
$OmniArgs = "-f `"$Config`" -datadir `"$DataDir`""

$Process = Start-Process `
    -FilePath $Omni `
    -ArgumentList $OmniArgs `
    -WorkingDirectory $PackageRoot `
    -RedirectStandardOutput $Stdout `
    -RedirectStandardError $Stderr `
    -WindowStyle Hidden `
    -PassThru

Set-Content -Path $PidFile -Value $Process.Id

Write-Host "Started Chain33 ticket+EVM node with PID $($Process.Id)."
Write-Host "Config: $Config"
Write-Host "Web3 RPC: http://127.0.0.1:8545"
Write-Host "Chain33 JSON-RPC: http://127.0.0.1:8801"

if (-not $NoBootstrap) {
    node $Monitor --rpc http://127.0.0.1:8801 --maintainers $Maintainers
}
