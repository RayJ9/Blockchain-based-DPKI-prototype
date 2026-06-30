# Fig5 Lambda Experiment

This folder is dedicated to the lambda sweep figure only.

Replot the figure from the retained CSV data:

```powershell
python Fig5-lambda\replot_figure.py
```

Output layout:

- Final figure files are written directly under this folder: `figure.png` and `figure.eps`.
- `figure_data.csv` contains measured points and fitted plot curves.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- `manifest.json` records the source run settings used to produce the retained data.

Current parameter choice:

- `gamma = 0.1`
- `lambda = 2,3,4,5,6,7,8,10,12,14`
- `meanBlockMs = 80,30,10`, estimated to produce roughly
  `lambda_p = 8/s, 15/s, 24/s` on the current local PoW setup.
- PKI is intentionally omitted from this figure.
