# Reproduction Status

This package keeps both final figures and experiment entry points. The restored
chain/prototype components are:

- `DPKI-and-DID-platform-Lenovo/chain33-dpki-real-experiment`
- `DPKI-and-DID-platform-Lenovo/omnilink-pow-4nodes`
- `dpki-experiment-prototype`
- `pow-4nodes-runtime`
- `omnilink`
- `simu2-8-packaged`

## Figure Status

| Figure | Current status | Full experiment entry |
| --- | --- | --- |
| Fig3 | Reproducible from retained prototype-calibration data | Section VI.2 old temporary runner not recovered |
| Fig4 | Reproducible from retained four-baseline summary | Section VI.2 old temporary runner not recovered |
| Fig5 | Full prototype experiment restored | `python Fig5-lambda\run_fig5_lambda.py ...` |
| Fig6 | Full prototype experiment restored | `python Fig6-epsilon\run_fig6_epsilon.py ...` |
| Fig7 | Full prototype experiment restored | `python Fig7-p\run_fig7_p.py ...` |
| Fig8 | Full prototype experiment restored | `python Fig8-M\run_fig8_m.py ...` |
| Fig9 | Reproducible from retained Fig7-style availability source data | Source-data builder from the old temporary suite not recovered |
| Fig10 | Reproducible from retained Fig7-style availability source data | Source-data builder from the old temporary suite not recovered |

## Notes

- Fig5-Fig8 runners import common modules from `simu2-8-packaged` and use the
  restored Omnilink PoW runtime under `DPKI-and-DID-platform-Lenovo`.
- Fig3/Fig4/Fig9/Fig10 can regenerate their `.mat` data and final figures from
  retained source data.
- Runtime data, logs, outputs, and Node dependencies are intentionally ignored
  by Git through `.gitignore`.
- `JIoT/` and `response_letter/` are intentionally ignored by Git.
