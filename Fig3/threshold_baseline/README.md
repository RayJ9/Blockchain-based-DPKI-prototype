# Threshold-Validation DPKI Baseline

This folder contains an isolated baseline prototype for a threshold-validation
DPKI workflow. It does not modify any existing figure outputs.

The baseline uses `k-of-n` validator endorsements:

- default `n = 8`
- default `k = 4`
- the client sends validation requests to all 8 local validator HTTP endpoints
  in parallel and accepts the result after receiving 4 valid endorsements
- validator ports default to `23080` through `23087`
- assertion signing/verification is included in the certificate-verification
  stage through the Fig7-aligned anchor table
- management and on-chain authentication write a compact threshold receipt
  using contract-stage values anchored to the retained MPT-DPKI measurements

Run:

```powershell
python fig3\threshold_baseline\run_threshold_baseline.py --rounds 2000
```

For a quick smoke test:

```powershell
python fig3\threshold_baseline\run_threshold_baseline.py --rounds 20
```

Outputs:

- `threshold_request_metrics.csv`: per-request stages and costs
- `threshold_summary_by_request_class.csv`: summary rows with the same schema as
  `fig3/source_data/summary_by_request_class_fig7_aligned.csv`
- `summary_with_threshold_baseline.csv`: retained Section VI.2 summary plus this
  threshold baseline, for later plotting if needed
- `threshold_config.json`: run parameters

Request classes:

- `management`: certificate issue/update, certificate verification + assertion,
  threshold endorsement, on-chain update
- `intra-off-chain`: certificate verification + assertion, threshold
  validation, no chain write
- `intra-on-chain`: intra-domain threshold validation plus compact on-chain
  receipt
- `cross-on-chain`: cross-domain certificate-chain verification + assertion,
  threshold validation, compact on-chain receipt
