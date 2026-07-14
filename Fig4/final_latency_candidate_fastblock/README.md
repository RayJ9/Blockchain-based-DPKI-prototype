# Fig4 Fastblock Final-Latency Candidate

This folder restores the previously edited `fastblock` latency version as a
standalone candidate snapshot, without modifying the current `Fig4/` official
workflow.

## Included files

- `figure_latency_fastblock.{png,pdf,eps}`: retained fastblock latency figure.
- `generate_data_fig4_fastblock.py`
- `plot_fig4_fastblock.m`
- `data_fig4_fastblock.mat`
- `latency_distribution_summary_fastblock.csv`
- `PrintFigToPaper.m`

## Retained benchmark source

The fastblock benchmark output used by this candidate is retained under:

- `prototype_baseline_benchmark/outputs/fastblock_1ms_2000_20260706_201806_flow_corrected/`

For convenience, its summary CSV is also copied to:

- `source_data/summary_by_request_class_fastblock.csv`

## Purpose

Use this folder when you want to inspect or recover the last edited
`figure_latency_fastblock` version, while keeping the current `Fig4/` files
unchanged.
