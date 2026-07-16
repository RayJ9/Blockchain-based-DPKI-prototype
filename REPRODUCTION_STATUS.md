# Reproduction Status

This package keeps the files needed to regenerate the paper experiments in
semantically named folders under `experiments/`.

## Restored Prototype Components

- `omnilink`
- `dpki-experiment-prototype`
- `pow-4nodes-runtime`
- `simu2-8-packaged`
- `simu2_tail_prob`

## Figure Status

| Paper figure | Experiment | Current status | Full experiment entry |
| --- | --- | --- | --- |
| Fig. 3 | `pow-interval-validation` | Reproducible from retained prototype-calibration data | Retained-data generator |
| Fig. 4 | `baseline-comparison` | Reproducible from retained four-baseline summary | `experiments\baseline-comparison\run_experiment.ps1` |
| Fig. 5 | `arrival-rate` | Full prototype experiment entry restored | `python experiments\arrival-rate\run_fig5_lambda.py ...` |
| Fig. 6 | `cross-domain-ratio` | Full prototype experiment entry restored | `python experiments\cross-domain-ratio\run_fig6_epsilon.py ...` |
| Fig. 7 | `management-ratio` | Full prototype experiment entry restored | `python experiments\management-ratio\run_fig7_p.py ...` |
| Fig. 8 | `service-ca-number` | Full prototype experiment entry restored | `python experiments\service-ca-number\run_fig8_m.py ...` |
| Fig. 9 | `availability-timeout` | Reproducible from retained availability source data | Lightweight real-chain probe |
| Fig. 10 | `availability-service-ca-number` | Reproducible from retained availability source data | Lightweight real-chain probe |

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

- The parameter-sweep runners import common modules from `simu2-8-packaged` and use
  `dpki-experiment-prototype` together with `pow-4nodes-runtime`.
- The PoW validation, baseline comparison, and availability experiments can regenerate their `.mat` data and final figures from
  retained source data.
- Runtime data, logs, outputs, local Node dependencies, recovered backups, and
  private manuscript folders are intentionally ignored by Git.
