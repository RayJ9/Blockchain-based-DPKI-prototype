$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

python .\generate_data_fig4.py

$matlabExe = "C:\Program Files\MATLAB\R2024a\bin\matlab.exe"
if (-not (Test-Path $matlabExe)) {
    $matlabExe = "matlab"
}

$matlabDir = (Resolve-Path $PSScriptRoot).Path.Replace("\", "/")
& $matlabExe -batch "cd('$matlabDir'); plot_fig4"
