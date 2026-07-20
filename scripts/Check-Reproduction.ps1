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
    "blockchain\platform_registry.js",
    "blockchain\platforms\centralized-pki\index.js",
    "blockchain\platforms\centralized-pki\platform.json",
    "blockchain\platforms\proposed-dpki\index.js",
    "blockchain\platforms\proposed-dpki\contracts\ProposedDPKI.sol",
    "blockchain\platforms\multi-ca-dpki\index.js",
    "blockchain\platforms\multi-ca-dpki\contracts\ThresholdValidationDPKI.sol",
    "blockchain\platforms\full-contract-dpki\index.js",
    "blockchain\platforms\full-contract-dpki\contracts\FullContractDPKI.sol",
    "blockchain\sidechain-three-chain\run_experiment.ps1",
    "blockchain\sidechain-three-chain\run-sidechain-smoke.js",
    "blockchain\sidechain-three-chain\scripts\start-three-chains.ps1",
    "blockchain\sidechain-three-chain\scripts\stop-three-chains.ps1",
    "blockchain\sidechain-three-chain\contracts\MainChainCARegistry.sol",
    "blockchain\sidechain-three-chain\contracts\SidechainDPKI.sol",
    "omnilink",
    "blockchain\dpki-experiment",
    "blockchain\dpki-experiment\package.json",
    "blockchain\dpki-experiment\package-lock.json",
    "blockchain\dpki-experiment\run-real-dpki-experiment.js",
    "blockchain\dpki-experiment\contracts\DPKIExperiment.sol",
    "blockchain\pow-4nodes-runtime",
    "blockchain\pow-4nodes-runtime\scripts\start-omnilink-pow-4nodes.ps1",
    "blockchain\pow-4nodes-runtime\scripts\stop-omnilink-pow-4nodes.ps1",
    ".internal\legacy-simulations\simu2-8-packaged\real_figure_sweep_common.py",
    ".internal\legacy-simulations\simu2_tail_prob\real_sweep_figures.py",
    "experiments\pow-interval-validation\generate_data_fig3.py",
    "experiments\pow-interval-validation\plot_fig3.m",
    "experiments\pow-interval-validation\run_experiment.ps1",
    "experiments\baseline-comparison\generate_data_fig4.py",
    "experiments\baseline-comparison\plot_fig4.m",
    "experiments\baseline-comparison\run_experiment.ps1",
    "experiments\baseline-comparison\prototype_baseline_benchmark\run_prototype_baseline_benchmark.js",
    "experiments\baseline-comparison\prototype_baseline_benchmark\contracts\Fig4BaselineBenchmark.sol",
    "experiments\arrival-rate\run_fig5_lambda.py",
    "experiments\arrival-rate\run_experiment.ps1",
    "experiments\arrival-rate\replot_figure.py",
    "experiments\cross-domain-ratio\run_fig6_epsilon.py",
    "experiments\cross-domain-ratio\run_experiment.ps1",
    "experiments\cross-domain-ratio\replot_figure.py",
    "experiments\management-ratio\run_fig7_p.py",
    "experiments\management-ratio\run_experiment.ps1",
    "experiments\management-ratio\replot_figure.py",
    "experiments\service-ca-number\run_fig8_m.py",
    "experiments\service-ca-number\run_experiment.ps1",
    "experiments\service-ca-number\replot_figure.py",
    "experiments\availability-timeout\generate_data_fig9.py",
    "experiments\availability-timeout\run_experiment.ps1",
    "experiments\availability-timeout\plot_fig9.m",
    "experiments\availability-service-ca-number\generate_data_fig10.py",
    "experiments\availability-service-ca-number\run_experiment.ps1",
    "experiments\availability-service-ca-number\plot_fig10.m",
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
        "experiments\pow-interval-validation\generate_data_fig3.py",
        "experiments\baseline-comparison\generate_data_fig4.py",
        "experiments\arrival-rate\run_fig5_lambda.py",
        "experiments\arrival-rate\replot_figure.py",
        "experiments\cross-domain-ratio\run_fig6_epsilon.py",
        "experiments\cross-domain-ratio\replot_figure.py",
        "experiments\management-ratio\run_fig7_p.py",
        "experiments\management-ratio\replot_figure.py",
        "experiments\service-ca-number\run_fig8_m.py",
        "experiments\service-ca-number\replot_figure.py",
        "experiments\availability-timeout\generate_data_fig9.py",
        "experiments\availability-timeout\convert_png_to_pdf_eps.py",
        "experiments\availability-service-ca-number\generate_data_fig10.py",
        "scripts\Extract-TailProbe.py",
        "figure_dpki_pki_runtime\backend.py",
        "figure_dpki_pki_runtime\sweep_common.py",
        "figure_dpki_pki_runtime\epsilon_metrics.py",
        "figure_dpki_pki_runtime\availability_common.py"
    )
    python -m py_compile @PythonFiles
}

python experiments\arrival-rate\run_fig5_lambda.py --help | Out-Null
python experiments\cross-domain-ratio\run_fig6_epsilon.py --help | Out-Null
python experiments\management-ratio\run_fig7_p.py --help | Out-Null
python experiments\service-ca-number\run_fig8_m.py --help | Out-Null

if (Test-Path -LiteralPath "blockchain\dpki-experiment\node_modules\solc") {
    node scripts\Check-ModuleContracts.js | Out-Null
}

Write-Host "Reproduction check passed. Required platform modules and semantic experiment entry points are present."
