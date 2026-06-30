# Fig6 Epsilon Experiment

This folder is dedicated to the epsilon figure only. It does not change the
other final figures.

Run the full epsilon experiment through the prototype and Omnilink PoW chain:

```powershell
python Fig6-epsilon\run_fig6_epsilon.py --requests 2000 --stop-pow
```

Replot the figure from the retained CSV data only:

```powershell
python Fig6-epsilon\replot_figure.py
```

Output layout:

- Final figure files are written directly under this folder:
  `figure.png`, `figure.eps`, and their CSV sources.
- `figure_data.csv` contains both measured points and fitted plot curves. The
  `dataKind` column separates `measured_point` from `plot_curve`.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- `manifest.json` records the source run settings used to produce the retained data.

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
