# Arrival-Rate Polished Plot

This folder contains a non-destructive single-anchor-theory variant of the
arrival-rate experiment.

- The original figure in the parent experiment directory is not modified.
- `source_figure_data.csv` is a copy of the retained original data.
- `build_polished_fig5.py` regenerates a `lambda = 14` anchor-theory variant.
  For each `lambda_p` curve, the script takes the measured parameter set at
  `lambda = 14` as the only calibration source, then recomputes the theoretical
  upper/lower bounds for the full lambda sweep.
- The measured markers are kept as points, while the experimental trend is drawn
  as a separate smoothed monotone curve instead of forcing the line to pass
  through every point.

Rebuild:

```powershell
python experiments\arrival-rate\polished-plot\build_polished_fig5.py
```

The script exports:

- `figure.png`
- `figure.pdf`
- `figure.eps`
- `figure_data.csv`
