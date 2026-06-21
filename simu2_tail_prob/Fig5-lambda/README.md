# Fig5 Lambda Experiment

This folder is dedicated to the lambda sweep figure only.

Run the figure from existing raw experiment runs:

```powershell
python simu2_tail_prob\Fig5-lambda\run_fig5_lambda.py --lambda-values 2,3,4,5,6,7,8,10,12,14 --mean-block-ms-values 80,30,10 --requests 200 --tag lambda_scout --stop-pow
```

Output layout:

- Final figure files are written directly under this folder: `figure.png` and `figure.eps`.
- `figure_data.csv` contains measured points and fitted plot curves.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- The canonical run output is also written to `result/`.
- Consistency checks, transaction health, and raw run directories are written to `result/logs/`.

Current parameter choice:

- `gamma = 0.1`
- `lambda = 2,3,4,5,6,7,8,10,12,14`
- `meanBlockMs = 80,30,10`, estimated to produce roughly
  `lambda_p = 8/s, 15/s, 24/s` on the current local PoW setup.
- PKI is intentionally omitted from this figure.
