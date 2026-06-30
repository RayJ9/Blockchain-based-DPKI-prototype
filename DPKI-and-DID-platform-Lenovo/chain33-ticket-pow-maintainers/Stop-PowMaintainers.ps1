$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $Root "pow-maintainers.pid"

if (-not (Test-Path -LiteralPath $PidFile)) {
  Write-Host "No PoW maintainer PID file was found."
  exit 0
}

$PidValue = Get-Content -LiteralPath $PidFile | Select-Object -First 1
$Process = $null
if ($PidValue) {
  $Process = Get-Process -Id $PidValue -ErrorAction SilentlyContinue
}

if ($Process) {
  Stop-Process -Id $PidValue
  Write-Host "Stopped PoW maintainer network with PID $PidValue."
} else {
  Write-Host "PoW maintainer process $PidValue was not running."
}

Remove-Item -LiteralPath $PidFile -Force

