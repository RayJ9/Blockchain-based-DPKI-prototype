$ErrorActionPreference = "Stop"

$PackageRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$PidFile = Join-Path $PackageRoot "runtime\ticket-evm-fast.pid"

if (-not (Test-Path $PidFile)) {
    Write-Host "No Chain33 ticket+EVM PID file was found."
    exit 0
}

$PidValue = Get-Content $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
if ($PidValue -and (Get-Process -Id $PidValue -ErrorAction SilentlyContinue)) {
    Stop-Process -Id $PidValue -Force
    Write-Host "Stopped Chain33 ticket+EVM node with PID $PidValue."
} else {
    Write-Host "Chain33 ticket+EVM process $PidValue was not running."
}

Remove-Item $PidFile -ErrorAction SilentlyContinue
