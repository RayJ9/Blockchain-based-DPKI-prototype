param(
    [int]$Maintainers = 4,
    [string]$RpcUrl = "http://127.0.0.1:18801",
    [string]$DataDir = "",
    [switch]$NoBootstrap
)

$ErrorActionPreference = "Stop"

$PackageRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$ProjectRoot = (Resolve-Path (Split-Path -Parent $PackageRoot)).Path
$Omni = (Resolve-Path (Join-Path $ProjectRoot "bin\omni.exe")).Path
$Config = (Resolve-Path (Join-Path $PackageRoot "config\ticket-pow.toml")).Path
$Monitor = (Resolve-Path (Join-Path $PackageRoot "scripts\bootstrap-and-monitor.js")).Path

if (-not (Test-Path $Omni)) {
    throw "Cannot find omni.exe at $Omni"
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required for the bootstrap/monitor script."
}

if ([string]::IsNullOrWhiteSpace($DataDir)) {
    $DataDir = Join-Path $PackageRoot "runtime\node"
}

New-Item -ItemType Directory -Force $DataDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $PackageRoot "runtime") | Out-Null

$PidFile = Join-Path $PackageRoot "runtime\omni.pid"
if (Test-Path $PidFile) {
    $OldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($OldPid -and (Get-Process -Id $OldPid -ErrorAction SilentlyContinue)) {
        throw "omni.exe already appears to be running with PID $OldPid. Stop it first with scripts\stop-pow.ps1."
    }
}

Write-Host "[start] Chain33 ticket/PoW config: $Config"
Write-Host "[start] Runtime data dir: $DataDir"
Write-Host "[start] Required maintainers: $Maintainers"

$OmniArgs = "-f `"$Config`" -datadir `"$DataDir`""
$Process = Start-Process -FilePath $Omni -ArgumentList $OmniArgs -WorkingDirectory $PackageRoot -WindowStyle Hidden -PassThru
Set-Content -Path $PidFile -Value $Process.Id

try {
    $MonitorArgs = @($Monitor, "--rpc", $RpcUrl, "--maintainers", $Maintainers, "--watch")
    if ($NoBootstrap) {
        $MonitorArgs += "--no-bootstrap"
    }
    node @MonitorArgs
}
finally {
    if (Get-Process -Id $Process.Id -ErrorAction SilentlyContinue) {
        Stop-Process -Id $Process.Id -Force
    }
    Remove-Item $PidFile -ErrorAction SilentlyContinue
}
