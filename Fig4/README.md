# Fig4

Section VI.2 baseline-latency and cost comparison figure.

This figure is generated from the retained baseline summary:

- `source_data/summary_by_request_class_no_authsig.csv`

The summary covers the proposed DPKI, traditional PKI, OCSP-on-chain baseline,
and full-contract on-chain baseline.

The older temporary runner that produced this four-baseline summary was not
found in the recovered backups. The retained CSV keeps the measured values and
schema needed to reproduce the paper figure. A rebuilt baseline runner should
write the same CSV schema before running this script.

Rebuild the figure data and redraw:

```powershell
python generate_data_fig4.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('Fig4'); plot_fig4"
```

Outputs:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig4.mat`
- `source_data/summary_by_request_class_no_authsig.csv`
