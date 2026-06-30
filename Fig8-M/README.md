# Fig8 M Experiment

This folder is dedicated to the service-node count sweep figure only.

Replot the figure from the retained CSV data:

```powershell
python Fig8-M\replot_figure.py
```

Output layout:

- Final figure files are written directly under this folder: `figure.png` and `figure.eps`.
- `figure_data.csv` contains measured points and fitted plot curves.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- `manifest.json` records the source run settings used to produce the retained data.
