$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

node .\prototype_baseline_benchmark\run_prototype_baseline_benchmark.js --requests 1 --actual-overhead
python .\generate_overhead_cost_table.py
python .\plot_overhead_cost_table.py
