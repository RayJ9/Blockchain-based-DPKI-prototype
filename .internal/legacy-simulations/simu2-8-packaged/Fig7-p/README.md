# Fig7 p Experiment

This folder is dedicated to the management-ratio sweep figure only.

Run the figure from existing raw experiment runs:

```powershell
python simu2_tail_prob\Fig7-p\run_fig7_p.py --p-values 0.05,0.1,0.15,0.2 --requests 500 --lambda-arrival 2 --tag final_candidate_lambda2_r500 --reuse-existing --no-restart-pow
```

Output layout:

- Final figure files are written directly under this folder: `figure.png` and `figure.eps`.
- `figure_data.csv` contains measured points and fitted plot curves.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- The canonical run output is also written to `result/`.
- Consistency checks, transaction health, and raw run directories are written to `result/logs/`.
