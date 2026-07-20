param([int]$Requests = 10)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
foreach ($Figure in 4..10) {
    & (Join-Path $Root "scripts\Run-FigureExperiment.ps1") -Figure $Figure -Requests $Requests
}
Write-Host "All semantic experiment smoke runs completed."
