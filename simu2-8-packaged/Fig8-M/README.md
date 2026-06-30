# Fig8 M Experiment

This folder is dedicated to the service-node count sweep figure only.

Run the figure from existing raw experiment runs:

```powershell
python simu2_tail_prob\Fig8-M\run_fig8_m.py --m-values 2,4,8 --requests 500 --lambda-arrival 6 --seed 84001 --tag final_candidate_lambda6_r500_seed84001 --reuse-existing --no-restart-pow
```

Output layout:

- Final figure files are written directly under this folder: `figure.png` and `figure.eps`.
- `figure_data.csv` contains measured points and fitted plot curves.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- The canonical run output is also written to `result/`.
- Consistency checks, transaction health, and raw run directories are written to `result/logs/`.
