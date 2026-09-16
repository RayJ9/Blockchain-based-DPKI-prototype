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
    if ($LASTEXITCODE -ne 0) { throw "Replot step failed: $Name" }
}

# No source measurements are distributed with the repository. Check every
# input before generating data or replacing any retained image.
$RequiredInputs = @(
    "experiments\pow-interval-validation\source_data\strict_pow_clock_samples.csv",
    "experiments\baseline-comparison\source_data\summary_by_request_class_fastblock.csv",
    "experiments\arrival-rate\figure_data.csv",
    "experiments\cross-domain-ratio\figure_data.csv",
    "experiments\management-ratio\figure_data.csv",
    "experiments\service-ca-number\figure_data.csv",
    "experiments\availability-timeout\source_data\surface_data_matrices_responding.npz",
    "experiments\availability-timeout\source_data\surface_data_matrices_malicious.npz",
    "experiments\availability-service-ca-number\source_data\availability_pf_m_slices_responding.csv",
    "experiments\availability-service-ca-number\source_data\availability_pf_m_slices_malicious.csv"
)
$MissingInputs = @($RequiredInputs | Where-Object { -not (Test-Path -LiteralPath $_) })
if ($MissingInputs.Count -gt 0) {
    throw "Source measurements are not bundled. Supply new, traceable measurements before replotting. Missing: $($MissingInputs -join ', ')"
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

Invoke-Step "Generate PoW interval validation data" { python experiments\pow-interval-validation\generate_data_fig3.py }
Invoke-Step "Generate baseline comparison data" { python experiments\baseline-comparison\generate_data_fig4.py }
Invoke-Step "Replot arrival-rate experiment" { python experiments\arrival-rate\replot_figure.py }
Invoke-Step "Replot cross-domain-ratio experiment" { python experiments\cross-domain-ratio\replot_figure.py }
Invoke-Step "Replot management-ratio experiment" { python experiments\management-ratio\replot_figure.py }
Invoke-Step "Replot service-CA-number experiment" { python experiments\service-ca-number\replot_figure.py }
Invoke-Step "Generate availability-timeout data" { python experiments\availability-timeout\generate_data_fig9.py }
Invoke-Step "Generate availability-service-CA-number data" { python experiments\availability-service-ca-number\generate_data_fig10.py }

Invoke-Step "Draw PoW interval validation with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/experiments/pow-interval-validation'); plot_fig3" }
Invoke-Step "Draw baseline comparison with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/experiments/baseline-comparison'); plot_fig4" }
Invoke-Step "Draw availability-timeout with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/experiments/availability-timeout'); plot_fig9" }
Invoke-Step "Draw availability-service-CA-number with MATLAB" { & $MatlabCommand -batch "cd('$MatlabRoot/experiments/availability-service-ca-number'); plot_fig10" }

Write-Host "Replotting from locally supplied measurements completed."
