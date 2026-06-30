param(
    [switch]$SkipPythonCompile
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RequiredPaths = @(
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
    "Fig5-lambda\run_fig5_lambda.py",
    "Fig5-lambda\replot_figure.py",
    "Fig6-epsilon\run_fig6_epsilon.py",
    "Fig6-epsilon\replot_figure.py",
    "Fig7-p\run_fig7_p.py",
    "Fig7-p\replot_figure.py",
    "Fig8-M\run_fig8_m.py",
    "Fig8-M\replot_figure.py",
    "Fig9\generate_data_fig9.py",
    "Fig9\plot_fig9.m",
    "Fig10\generate_data_fig10.py",
    "Fig10\plot_fig10.m"
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
        "Fig10\generate_data_fig10.py"
    )
    python -m py_compile @PythonFiles
}

python Fig5-lambda\run_fig5_lambda.py --help | Out-Null
python Fig6-epsilon\run_fig6_epsilon.py --help | Out-Null
python Fig7-p\run_fig7_p.py --help | Out-Null
python Fig8-M\run_fig8_m.py --help | Out-Null

Write-Host "Reproduction check passed. Required source folders, figure scripts, and Fig5-Fig8 experiment entry points are present."
