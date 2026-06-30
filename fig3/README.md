# Fig3

Section VI.2 prototype-calibration figure.

Run:

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
