param(
    [switch]$SkipPythonCompile
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RequiredPaths = @(
    "package.json",
    "requirements.txt",
    "platform_registry.js",
    "platform_traditional_pki\index.js",
    "platform_traditional_pki\platform.json",
    "platform_proposed_dpki\index.js",
    "platform_proposed_dpki\contracts\ProposedDPKI.sol",
    "platform_threshold_dpki\index.js",
    "platform_threshold_dpki\contracts\ThresholdValidationDPKI.sol",
    "platform_full_contract_dpki\index.js",
    "platform_full_contract_dpki\contracts\FullContractDPKI.sol",
    "omnilink",
    "dpki-experiment-prototype",
    "dpki-experiment-prototype\package.json",
    "dpki-experiment-prototype\package-lock.json",
    "dpki-experiment-prototype\run-real-dpki-experiment.js",
    "dpki-experiment-prototype\contracts\DPKIExperiment.sol",
    "pow-4nodes-runtime",
    "pow-4nodes-runtime\scripts\start-omnilink-pow-4nodes.ps1",
    "pow-4nodes-runtime\scripts\stop-omnilink-pow-4nodes.ps1",
    "simu2-8-packaged\real_figure_sweep_common.py",
    "Fig3\generate_data_fig3.py",
    "Fig3\plot_fig3.m",
    "Fig4\generate_data_fig4.py",
    "Fig4\plot_fig4.m",
    "Fig4\run_experiment.ps1",
    "Fig4\prototype_baseline_benchmark\run_prototype_baseline_benchmark.js",
    "Fig4\prototype_baseline_benchmark\contracts\Fig4OverheadBenchmark.sol",
    "Fig5-lambda\run_fig5_lambda.py",
    "Fig5-lambda\run_experiment.ps1",
    "Fig5-lambda\replot_figure.py",
    "Fig6-epsilon\run_fig6_epsilon.py",
    "Fig6-epsilon\run_experiment.ps1",
    "Fig6-epsilon\replot_figure.py",
    "Fig7-p\run_fig7_p.py",
    "Fig7-p\run_experiment.ps1",
    "Fig7-p\replot_figure.py",
    "Fig8-M\run_fig8_m.py",
    "Fig8-M\run_experiment.ps1",
    "Fig8-M\replot_figure.py",
    "Fig9\generate_data_fig9.py",
    "Fig9\run_experiment.ps1",
    "Fig9\plot_fig9.m",
    "Fig10\generate_data_fig10.py",
    "Fig10\run_experiment.ps1",
    "Fig10\plot_fig10.m",
    "scripts\Setup-Environment.ps1",
    "scripts\Run-FigureExperiment.ps1",
    "scripts\Collect-ExperimentArtifacts.ps1",
    "scripts\Extract-TailProbe.py",
    "scripts\Check-ModuleContracts.js",
    ".github\workflows\reproduction-check.yml"
)

foreach ($Path in $RequiredPaths) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing required reproduction path: $Path"
    }
}

if (-not $SkipPythonCompile) {
    $PythonFiles = @(
        "Fig3\generate_data_fig3.py",
        "Fig4\generate_data_fig4.py",
        "Fig5-lambda\run_fig5_lambda.py",
        "Fig5-lambda\replot_figure.py",
        "Fig6-epsilon\run_fig6_epsilon.py",
        "Fig6-epsilon\replot_figure.py",
        "Fig7-p\run_fig7_p.py",
        "Fig7-p\replot_figure.py",
        "Fig8-M\run_fig8_m.py",
        "Fig8-M\replot_figure.py",
        "Fig9\generate_data_fig9.py",
        "Fig9\convert_png_to_pdf_eps.py",
        "Fig10\generate_data_fig10.py",
        "scripts\Extract-TailProbe.py",
        "figure_dpki_pki_runtime\backend.py",
        "figure_dpki_pki_runtime\sweep_common.py",
        "figure_dpki_pki_runtime\epsilon_metrics.py",
        "figure_dpki_pki_runtime\availability_common.py"
    )
    python -m py_compile @PythonFiles
}

python Fig5-lambda\run_fig5_lambda.py --help | Out-Null
python Fig6-epsilon\run_fig6_epsilon.py --help | Out-Null
python Fig7-p\run_fig7_p.py --help | Out-Null
python Fig8-M\run_fig8_m.py --help | Out-Null

if (Test-Path -LiteralPath "dpki-experiment-prototype\node_modules\solc") {
    node scripts\Check-ModuleContracts.js | Out-Null
}

Write-Host "Reproduction check passed. Required source folders, figure scripts, and Fig5-Fig8 experiment entry points are present."
