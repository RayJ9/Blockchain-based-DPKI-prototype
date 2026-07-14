# Fig4

Run a new isolated real-chain comparison of all four platforms:

```powershell
Fig4\run_experiment.ps1 -Requests 50
```

Use `-PaperScale` for the paper request count. New results, certificates,
receipts, node logs, and the console transcript are written under
`experiment_artifacts/Fig4`; the retained figure files in this folder are not
overwritten.

This directory now keeps only the final Section VI.2 artifacts and the scripts
needed to reproduce them:

- `figure_latency.*`: final latency comparison figure.
- `figure_overhead_table.*`: final overhead table figure.
- `overhead_cost_table.{csv,md,tex}`: exact overhead values used by the table
  figure.

## 1. Latency figure

The latency figure is built from the retained baseline summaries:

- `source_data/summary_by_request_class_fig7_aligned.csv`
- `source_data/threshold_summary_by_request_class.csv`
- `full_contract_baseline/full_contract_summary_by_request_class.csv`

`generate_data_fig4.py` now reads the retained fastblock latency run under
`final_latency_candidate_fastblock/prototype_baseline_benchmark/outputs/`,
rewrites the latency stages into a paper-facing split
`Packaging delay -> On-chain execution -> remaining workflow stages`, writes
`data_fig4.mat`, and exports `latency_distribution_summary.csv`. `plot_fig4.m`
then draws the final `figure_latency.*` assets in the main `Fig4/` directory.

Reproduce:

```powershell
.\reproduce_latency.ps1
```

or run the two steps manually:

```powershell
python .\generate_data_fig4.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('Fig4'); plot_fig4"
```

## 2. Overhead figure

The overhead table figure is rebuilt from the Fig4-specific prototype benchmark:

- benchmark: `prototype_baseline_benchmark/run_prototype_baseline_benchmark.js`
- contract: `prototype_baseline_benchmark/contracts/Fig4OverheadBenchmark.sol`
- latest retained run: `prototype_baseline_benchmark/outputs/actual_overhead_stagebreakdown_receiptgas_onegroup_rich_20260708_3`

`generate_overhead_cost_table.py` reads the latest retained overhead run and
exports:

- `overhead_cost_table.csv`
- `overhead_cost_table.md`
- `overhead_cost_table.tex`

`plot_overhead_cost_table.py` renders `figure_overhead_table.*`.

Reproduce:

```powershell
.\reproduce_overhead.ps1
```

or run the three steps manually:

```powershell
node .\prototype_baseline_benchmark\run_prototype_baseline_benchmark.js --requests 1 --actual-overhead
python .\generate_overhead_cost_table.py
python .\plot_overhead_cost_table.py
```

## 3. Retained experiment data

- `data_fig4.mat`
- `latency_distribution_summary.csv`
- `full_contract_baseline/full_contract_request_metrics.csv`
- `full_contract_baseline/full_contract_summary_by_request_class.csv`
- `prototype_baseline_benchmark/outputs/actual_overhead_stagebreakdown_receiptgas_onegroup_rich_20260708_3`

Anything else previously used during intermediate drafts has been removed from
`Fig4` so the folder matches the final paper workflow.

## 4. Fastblock latency snapshot

The retained fastblock latency source run and its historical intermediate
artifacts are still kept under:

- `final_latency_candidate_fastblock/`

The main `Fig4/figure_latency.*` files now use this fastblock-based latency
workflow, while the subfolder is preserved as a traceable source snapshot.
