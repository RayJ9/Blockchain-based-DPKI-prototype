# Fig7 p Experiment

This folder is dedicated to the management-ratio sweep figure only.

Run the full management-ratio experiment through the prototype and Omnilink PoW chain:

```powershell
Fig7-p\run_experiment.ps1 -PaperScale
```

For a custom isolated run, use `run_fig7_p.py` with an explicit
`--output-dir`; omitting it targets the figure-owned result path.

Replot the figure from the retained CSV data only:

```powershell
python Fig7-p\replot_figure.py
```

Output layout:

- Final figure files are written directly under this folder: `figure.png` and `figure.eps`.
- `figure_data.csv` contains measured points and fitted plot curves.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- `manifest.json` records the source run settings used to produce the retained data.
