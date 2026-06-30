# Fig8 M Experiment

This folder is dedicated to the service-node count sweep figure only.

Run the full service-node count experiment through the prototype and Omnilink PoW chain:

```powershell
python Fig8-M\run_fig8_m.py --m-values 2,3,4,5,6,7,8,9 --requests 10000 --stop-pow
```

Replot the figure from the retained CSV data only:

```powershell
python Fig8-M\replot_figure.py
```

Output layout:

- Final figure files are written directly under this folder: `figure.png` and `figure.eps`.
- `figure_data.csv` contains measured points and fitted plot curves.
- `delay_by_request_type.csv` contains per-request-type latency statistics.
- `manifest.json` records the source run settings used to produce the retained data.
