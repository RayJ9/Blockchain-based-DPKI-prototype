$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $PackageRoot "runtime\omni.pid"

if (-not (Test-Path $PidFile)) {
    Write-Host "No Chain33 ticket/PoW PID file found."
    exit 0
}

$PidValue = Get-Content $PidFile -ErrorAction SilentlyContinue
if ($PidValue -and (Get-Process -Id $PidValue -ErrorAction SilentlyContinue)) {
    Stop-Process -Id $PidValue -Force
    Write-Host "Stopped omni.exe PID $PidValue"
}
else {
    Write-Host "PID file existed, but the process is not running."
}

Remove-Item $PidFile -ErrorAction SilentlyContinue
