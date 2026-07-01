# Fig3

Section VI.2 prototype-calibration figure.

This figure is generated from retained prototype measurements:

- `source_data/summary_by_request_class_fig7_aligned.csv`
- `source_data/data_pow_exponential.mat`

The first file is the Fig7-aligned request-stage summary used by Fig3/Fig4. It
includes assertion signing/verification in the certificate-verification stage.
The second file is the PoW inter-block interval sample used for the exponential
distribution check.

`source_data/summary_by_request_class_no_authsig.csv` is retained only as the
old intermediate microbenchmark table. Do not use it directly for the paper
figure unless intentionally reproducing that old accounting style.

An isolated threshold-validation DPKI baseline prototype is provided under
`threshold_baseline/`. It writes separate CSV files and does not change this
figure unless its combined summary is explicitly used later.

Rebuild the figure data and redraw:

```powershell
python generate_data_fig3.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('Fig3'); plot_fig3"
```

Outputs:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig3.mat`
- `source_data/summary_by_request_class_fig7_aligned.csv`
- `source_data/summary_by_request_class_no_authsig.csv`
- `source_data/data_pow_exponential.mat`
