# PoW Poisson Validation

This experiment validates the block-production process used by the local
Omnilink/Chain33 PoW prototype. It is intentionally separated from the DPKI
workload experiments: the chain is run with empty-block mining enabled, and the
observer records when the block height changes.

## Run

Start the PoW prototype with empty-block mining. Use a moderate mean block
interval so the observer can resolve individual blocks through RPC polling.

```powershell
.\blockchain\pow-4nodes-runtime\scripts\start-omnilink-pow-4nodes.ps1 -Clean -MeanBlockMs 500 -MineEmpty
```

Collect a block-height trace:

```powershell
python .\simu2_tail_prob\pow_poisson_validation\collect_pow_block_trace.py `
  --duration-sec 900 `
  --warmup-sec 30 `
  --poll-ms 10 `
  --output-dir .\simu2_tail_prob\pow_poisson_validation\result
```

Analyze the trace and generate figures:

```powershell
python .\simu2_tail_prob\pow_poisson_validation\analyze_pow_block_trace.py `
  --input-dir .\simu2_tail_prob\pow_poisson_validation\result `
  --window-sec 5
```

Stop the prototype when finished:

```powershell
.\blockchain\pow-4nodes-runtime\scripts\stop-omnilink-pow-4nodes.ps1
```

## Outputs

- `block_trace.csv`: block-height changes observed through RPC.
- `block_events.csv`: reconstructed block event times.
- `collection_manifest.json`: collection settings and block-count summary.
- `block_intervals.csv`: inter-block intervals used for fitting.
- `interarrival_statistics.csv`: fitted exponential statistics.
- `window_count_distribution.csv`: fixed-window block-count distribution.
- `summary.json`: machine-readable validation summary.
- `figure.png` and `figure.eps`: empirical interval CDF, Q-Q plot, and
  fixed-window count comparison with the fitted Poisson distribution.

## Interpretation

For an exponential inter-block interval, the coefficient of variation should be
close to one, the empirical CDF and Q-Q plot should align with the fitted
exponential curve, and the number of blocks in fixed-length windows should
match a Poisson distribution with mean `lambda_p * window_sec`.
