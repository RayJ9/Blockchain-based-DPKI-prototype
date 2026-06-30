$ErrorActionPreference = "Stop"

$DpkiRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$RuntimeRoot = Join-Path $DpkiRoot "runtime"

if (-not (Test-Path $RuntimeRoot)) {
  Write-Host "No Omnilink PoW runtime directory found."
  exit 0
}

$pidFiles = Get-ChildItem -LiteralPath $RuntimeRoot -Filter "node*.pid" -ErrorAction SilentlyContinue
if (-not $pidFiles) {
  Write-Host "No Omnilink PoW PID files found."
  exit 0
}

foreach ($pidFile in $pidFiles) {
  $pidValue = [int](Get-Content -LiteralPath $pidFile.FullName)
  $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
  if ($process) {
    Stop-Process -Id $pidValue -Force
    Wait-Process -Id $pidValue -Timeout 5 -ErrorAction SilentlyContinue
    Write-Host "Stopped $($pidFile.BaseName) PID $pidValue."
  } else {
    Write-Host "$($pidFile.BaseName) PID $pidValue was not running."
  }
  Remove-Item -LiteralPath $pidFile.FullName -Force
}

$allPidFile = Join-Path $RuntimeRoot "omnilink-pow-4nodes.pids"
if (Test-Path $allPidFile) {
  Remove-Item -LiteralPath $allPidFile -Force
}
