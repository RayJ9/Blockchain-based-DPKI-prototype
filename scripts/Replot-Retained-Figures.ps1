param(
    [string]$MatlabCommand = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host "==> $Name"
    & $Command
}

if ([string]::IsNullOrWhiteSpace($MatlabCommand)) {
    $MatlabFromPath = Get-Command matlab -ErrorAction SilentlyContinue
    if ($null -ne $MatlabFromPath) {
        $MatlabCommand = $MatlabFromPath.Source
    } else {
        $DefaultMatlab = "C:\Program Files\MATLAB\R2024a\bin\matlab.exe"
        if (-not (Test-Path -LiteralPath $DefaultMatlab)) {
            throw "MATLAB was not found in PATH or at $DefaultMatlab. Pass -MatlabCommand <path-to-matlab.exe>."
        }
        $MatlabCommand = $DefaultMatlab
    }
}

$MatlabRoot = ($Root -replace "\\", "/")

Invoke-Step "Generate Fig3 retained data" { python Fig3\generate_data_fig3.py }
Invoke-Step "Generate Fig4 retained data" { python Fig4\generate_data_fig4.py }
Invoke-Step "Replot Fig5 from retained CSV" { python Fig5-lambda\replot_figure.py }
Invoke-Step "Replot Fig6 from retained CSV" { python Fig6-epsilon\replot_figure.py }
Invoke-Step "Replot Fig7 from retained CSV" { python Fig7-p\replot_figure.py }
Invoke-Step "Replot Fig8 from retained CSV" { python Fig8-M\replot_figure.py }
Invoke-Step "Generate Fig9 retained data" { python Fig9\generate_data_fig9.py }
Invoke-Step "Generate Fig10 retained data" { python Fig10\generate_data_fig10.py }

Invoke-Step "Draw Fig3 with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/Fig3'); plot_fig3" }
Invoke-Step "Draw Fig4 with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/Fig4'); plot_fig4" }
Invoke-Step "Draw Fig9 with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/Fig9'); plot_fig9" }
Invoke-Step "Draw Fig10 with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/Fig10'); plot_fig10" }

Write-Host "Retained-data figure reproduction completed for Fig3-Fig10."
