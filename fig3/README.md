# Fig3

Section VI.2 prototype-calibration figure.

This figure is generated from retained prototype measurements:

- `source_data/summary_by_request_class_no_authsig.csv`
- `source_data/data_pow_exponential.mat`

The first file is the normalized request-stage summary used by Fig3/Fig4. The
second file is the PoW inter-block interval sample used for the exponential
distribution check.

The older temporary runner that produced the four-baseline Section VI.2 summary
was not found in the recovered backups. The retained CSV keeps the measured
values and schema needed to reproduce the paper figure. A rebuilt baseline
runner should write the same CSV schema before running this script.

Rebuild the figure data and redraw:

```powershell
python generate_data_fig3.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('fig3'); plot_fig3"
```

Outputs:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig3.mat`
- `source_data/summary_by_request_class_no_authsig.csv`
- `source_data/data_pow_exponential.mat`
