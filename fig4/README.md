# Fig4

Section VI.2 baseline-latency and cost comparison figure.

Run:

```powershell
python generate_data_fig4.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('fig4'); plot_fig4"
```

Outputs:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig4.mat`
- `source_data/summary_by_request_class_no_authsig.csv`
