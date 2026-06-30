# Fig10

Availability figure for failure probability and the number of service CAs.

The current source data are rebuilt from Fig7-style per-request service-time
samples by running:

```powershell
python ..\build_fig9_fig10_from_fig7_service.py
```

Run:

```powershell
python generate_data_fig10.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('fig10'); plot_fig10"
```

Outputs:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig10.mat`
- `figure_summary.csv`
- `source_data/fig7_service_latency_samples_summary.csv`
- `source_data/availability_pf_m_slices_responding.csv`
- `source_data/availability_pf_m_slices_malicious.csv`
