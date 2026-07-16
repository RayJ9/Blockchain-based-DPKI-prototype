# Availability-Service-CA-Number Experiment

Run the lightweight real-chain service-node/tail probe:

```powershell
experiments\availability-service-ca-number\run_experiment.ps1 -Requests 200
```

This executes a real service-CA-number run at `m=6` and extracts observed tail
statistics. It does not overwrite the retained availability surface data or final
figure.

Availability figure for failure probability and the number of service CAs.

The current source data are retained under `source_data/`. They were generated
from Fig7-style service-time measurements using the same DPKI/PKI intra-domain
service-time definition as Fig7.

Rebuild the figure data and redraw:

```powershell
python generate_data_fig10.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('experiments/availability-service-ca-number'); plot_fig10"
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
