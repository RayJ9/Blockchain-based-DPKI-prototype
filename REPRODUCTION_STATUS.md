# Reproduction Status

This package now keeps the files needed to regenerate Fig3-Fig10 in the top
level figure folders.

## Restored Prototype Components

- `omnilink`
- `dpki-experiment-prototype`
- `pow-4nodes-runtime`
- `simu2-8-packaged`
- `simu2_tail_prob`

## Figure Status

| Figure | Current status | Full experiment entry |
| --- | --- | --- |
| Fig3 | Reproducible from retained prototype-calibration data | Old Section VI.2 temporary baseline runner not recovered |
| Fig4 | Reproducible from retained four-baseline summary | Old Section VI.2 temporary baseline runner not recovered |
| Fig5 | Full prototype experiment entry restored | `python Fig5-lambda\run_fig5_lambda.py ...` |
| Fig6 | Full prototype experiment entry restored | `python Fig6-epsilon\run_fig6_epsilon.py ...` |
| Fig7 | Full prototype experiment entry restored | `python Fig7-p\run_fig7_p.py ...` |
| Fig8 | Full prototype experiment entry restored | `python Fig8-M\run_fig8_m.py ...` |
| Fig9 | Reproducible from retained Fig7-style availability source data | Old temporary availability builder not recovered |
| Fig10 | Reproducible from retained Fig7-style availability source data | Old temporary availability builder not recovered |

## Verification Commands

Quick structural check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Check-Reproduction.ps1
```

Replot final retained-data figures:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Replot-Retained-Figures.ps1
```

## Notes

- Fig5-Fig8 runners import common modules from `simu2-8-packaged` and use
  `dpki-experiment-prototype` together with `pow-4nodes-runtime`.
- Fig3/Fig4/Fig9/Fig10 can regenerate their `.mat` data and final figures from
  retained source data.
- Runtime data, logs, outputs, local Node dependencies, recovered backups, and
  private manuscript folders are intentionally ignored by Git.
