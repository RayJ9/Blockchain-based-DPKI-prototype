# Fig4

Section VI.2 baseline comparison figures.

This figure is generated from the Fig7-aligned baseline summary:

- `source_data/summary_by_request_class_fig7_aligned.csv`

The summary covers the proposed DPKI, traditional PKI, threshold-validation
DPKI, and full-contract on-chain baseline. The intermediate OCSP-on-chain
variant is intentionally excluded from the paper figure because it mixes the
OCSP status-query path with the on-chain authentication path and makes the stage
comparison harder to interpret. The certificate-verification stage includes
assertion signing/verification, so the total latency matches the Fig7 accounting
style.

If `../Fig3/threshold_baseline/threshold_summary_by_request_class.csv` exists,
the threshold-validation DPKI baseline is appended to Fig4 before plotting. This
baseline must be generated from the same Fig7-aligned anchor table.

`source_data/summary_by_request_class_no_authsig.csv` is retained only as the
old intermediate microbenchmark table. Do not use it directly for the paper
figure unless intentionally reproducing that old accounting style.

Rebuild the figure data and redraw:

```powershell
python generate_data_fig4.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('Fig4'); plot_fig4"
```

Current paper outputs:

- `figure_latency.png`
- `figure_latency.pdf`
- `figure_latency.eps`
- `figure_overhead.png`
- `figure_overhead.pdf`
- `figure_overhead.eps`

`figure_latency.*` contains the three latency panels for management,
intra-domain authentication, and cross-domain authentication. `figure_overhead.*`
contains the two on-chain authentication cost panels: gas overhead and complete
on-chain record overhead. The record overhead is computed as raw transaction
bytes, or transaction input bytes when the raw transaction size is unavailable,
plus receipt-log bytes and estimated state-write bytes. The management cost is
not included in the overhead figure because issuance and update/revocation
should be measured as separate management operations.

For the latency figure, `Assertion` covers the signed request/response message
and timestamp/nonce validity checking. For authentication requests, OCSP/MPT or
threshold checking and certificate/record checking are merged into `Service
processing`. For management requests, the status and certificate-validation
sub-stages are omitted because issuance/update and response assertion are the
meaningful comparable stages in this figure. Management issuance uses the
original service-probe measurement rather than the Fig7-aligned stage
allocation.

Legacy combined output retained for reference:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig4.mat`
- `source_data/summary_by_request_class_fig7_aligned.csv`
- `source_data/summary_by_request_class_no_authsig.csv`
- `../Fig3/threshold_baseline/threshold_summary_by_request_class.csv`
