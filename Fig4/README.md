# Fig4

Section VI.2 baseline comparison figures.

This figure is generated from the Fig7-aligned baseline summary:

- `source_data/summary_by_request_class_fig7_aligned.csv`

The summary covers the proposed DPKI, traditional PKI, OCSP-on-chain baseline,
and full-contract on-chain baseline. Its certificate-verification stage includes
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

Legacy combined output retained for reference:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig4.mat`
- `source_data/summary_by_request_class_fig7_aligned.csv`
- `source_data/summary_by_request_class_no_authsig.csv`
- `../Fig3/threshold_baseline/threshold_summary_by_request_class.csv`
