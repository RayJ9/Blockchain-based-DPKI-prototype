# Fig6 Epsilon Experiment

This folder is dedicated to the epsilon figure only. It does not change the
other final figures.

Run a full epsilon experiment:

```powershell
python simu2_tail_prob\Fig6-epsilon\run_fig6_epsilon.py --requests 2000 --stop-pow
```

Run a small one-point smoke test:

```powershell
python simu2_tail_prob\Fig6-epsilon\run_fig6_epsilon.py --epsilon-points 0.1 --requests 100 --stop-pow
```

Output layout:

- Final figure files are written directly under this folder:
  `figure.png`, `figure.eps`, and their CSV sources.
- The canonical run output is also written to `result/`.
- `figure_data.csv` contains both measured points and fitted plot curves. The
  `dataKind` column separates `measured_point` from `plot_curve`.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- Blockchain/runtime logs for the current run are copied to `result/logs/`
  with concise names such as `chain_transactions.csv`, `parameters.json`, and
  `bounds_check.csv`.
- Request-level and stage-level latency summaries are merged into
  `result/logs/latency_statistics.csv`.
- The script no longer creates timestamp/tag-style result folders by default.

Measurement choices:

- DPKI off-chain authentication uses cached domain roots via
  `--dpki-root-read-mode cache`; it does not scan the whole chain for every
  off-chain request.
- The Fig6 default on-chain intra-domain authentication ratio is
  `--gamma-on-chain 0.3`. When an older raw run is reused, the script replays
  the measured DPKI intra-domain samples at this ratio without rerunning the
  blockchain experiment.
- The actual service measurement stage uses `--actual-execution-mode serial`
  by default. Each DPKI/PKI operation still runs its real OpenSSL/MPT/on-chain
  work, while queueing is reconstructed from virtual arrivals and measured
  service times. This keeps synchronous OpenSSL work from blocking EVM raw-tx
  submission timers inside the Node.js event loop.
- DPKI off-chain, on-chain, cross-domain, and management all include their
  OpenSSL assertion sign/verify stages.
- DPKI management uses explicit stages, including certificate issuance,
  certificate verification, assertion, MPT build, the on-chain update, and a
  repository-update verification after the update is committed.
- PKI uses explicit OpenSSL/OCSP/assertion stage timing instead of outer
  Node.js wall-clock wrapper timing.
- PKI management excludes `pkiManagementOcspResponderRefresh`, treating the
  OCSP responder refresh as hot-update maintenance rather than the per-request
  service term.
- PKI management also verifies that the OpenSSL certificate repository contains
  the updated certificate after issuance.
