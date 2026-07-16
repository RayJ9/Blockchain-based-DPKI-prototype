$ErrorActionPreference = "Stop"

$PrototypeRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeRoot = Join-Path $PrototypeRoot "runtime"

if (-not (Test-Path -LiteralPath $RuntimeRoot)) {
    Write-Host "No three-chain runtime exists."
    exit 0
}

$stopped = 0
Get-ChildItem -LiteralPath $RuntimeRoot -Filter *.pid -File -ErrorAction SilentlyContinue | ForEach-Object {
    $pidValue = [int](Get-Content -LiteralPath $_.FullName)
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $pidValue -Force
        Write-Host "Stopped $($_.BaseName) PID $pidValue."
        $stopped += 1
    }
    Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
}

if ($stopped -eq 0) {
    Write-Host "No running three-chain processes found."
}
