# Baseline Latency Comparison

This experiment compares latency across the proposed DPKI, centralized PKI,
Multi-CA DPKI, and full-contract DPKI implementations.

Run a new isolated real-chain experiment:

```powershell
experiments\baseline-comparison\run_experiment.ps1 -Requests 50
```

Use `-PaperScale` for the paper request count. New measurements, certificates,
receipts, node logs, and the console transcript are written under
`experiment_artifacts/baseline-comparison`. Retained figure files in this
directory are not overwritten by an experiment run.

Request classes are mixed in a seeded round-robin order. The Multi-CA baseline
sends requests to six CA nodes concurrently and completes after four valid
responses. Our cross-domain workflow counts one end-to-end assertion. Its MPT
stage includes proof generation, the on-chain root query, proof-signer
verification, and Merkle-proof verification. Full-contract requests execute
X.509 path validation and the complete certificate, status, assertion, and
result-recording workflow; no synthetic sleep is added.

The experiment reports stage latency and latency distributions only. Raw chain
receipts remain in the run log for reproducibility, but communication, storage,
and gas are not aggregated or presented as comparison metrics.

## Retained latency assets

- `figure_latency.{eps,pdf,png}`: final latency comparison figure.
- `data_fig4.mat`: MATLAB input generated from the retained latency summary.
- `latency_distribution_summary.csv`: paper-facing latency stages and
  distribution statistics.
- `source_data/summary_by_request_class_fastblock.csv`: retained real-platform
  summary used to reproduce the figure.

## Reproduce the figure

```powershell
.\reproduce_latency.ps1
```

or run the two steps manually:

```powershell
python .\generate_data_fig4.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('experiments/baseline-comparison'); plot_fig4"
```

`generate_data_fig4.py` creates only latency inputs and summaries.
`plot_fig4.m` creates only `figure_latency.*`.
