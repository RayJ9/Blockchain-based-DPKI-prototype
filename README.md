# Blockchain-Based DPKI Experiment Package

This repository contains the prototype, retained experiment data, figure
scripts, and final figures for the revised experimental section of
"Blockchain-Based Decentralized Public Key Infrastructure Modeling and
Analysis".

The Git package is organized so that a fresh clone can regenerate the paper
figures. Runtime databases, logs, local Node dependencies, recovered backups,
private paper drafts, and temporary analysis folders are ignored by Git.

## Figure Folders

Each paper figure has one top-level folder:

| Figure | Folder | Reproduction mode |
| --- | --- | --- |
| Fig3 | `Fig3` | Regenerate from retained prototype-calibration data |
| Fig4 | `Fig4` | Regenerate from retained baseline-summary data |
| Fig5 | `Fig5-lambda` | Replot from retained CSV, or rerun prototype experiment |
| Fig6 | `Fig6-epsilon` | Replot from retained CSV, or rerun prototype experiment |
| Fig7 | `Fig7-p` | Replot from retained CSV, or rerun prototype experiment |
| Fig8 | `Fig8-M` | Replot from retained CSV, or rerun prototype experiment |
| Fig9 | `Fig9` | Regenerate from retained Fig7-style availability data |
| Fig10 | `Fig10` | Regenerate from retained Fig7-style availability data |

Every folder keeps the final `figure.*` files and the scripts/data needed to
recreate them. Fig5-Fig8 additionally keep `run_*.py` entry points for a
prototype rerun through Omnilink PoW.

## Required Components Kept in Git

Do not remove these folders from the reproducible package:

- `omnilink`: Omnilink source tree.
- `dpki-experiment-prototype`: DPKI prototype runner, contract, and Node
  dependency manifest.
- `pow-4nodes-runtime`: four-node Omnilink PoW runtime scripts.
- `simu2-8-packaged`: common queueing and real-sweep helpers used by Fig5-Fig8.
- `simu2_tail_prob`: compatibility simulation/module path still referenced by
  the prototype runner.

`JIoT/` and `response_letter/` are local manuscript/rebuttal folders and are
intentionally ignored.

## Dependencies

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

The retained-data figure path also needs MATLAB. Fig9 converts PNG to PDF/EPS
through `pdftops`, so Poppler must be available in `PATH` when redrawing Fig9.

For a full prototype rerun, install the Node dependencies used by the prototype:

```powershell
cd dpki-experiment-prototype
npm install
cd ..
```

Omnilink PoW runners may also need Go/PowerShell tooling depending on whether
the local Omnilink binaries already exist.

## Quick Integrity Check

Run this first after cloning:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Check-Reproduction.ps1
```

The script checks required source folders, compiles the Python entry points,
and verifies the Fig5-Fig8 experiment runners expose their command-line help.

## Recreate Final Figures from Retained Data

This is the fastest way to reproduce the paper figures without rerunning the
chain sweeps:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Replot-Retained-Figures.ps1
```

It regenerates Fig3/Fig4/Fig9/Fig10 data files, redraws Fig3/Fig4/Fig9/Fig10
with MATLAB, and replots Fig5-Fig8 from retained CSV outputs.

## Rerun Prototype Experiments for Fig5-Fig8

The Fig5-Fig8 `run_*.py` scripts can rerun the real prototype sweeps. They use
the Omnilink PoW runtime by default and write new run outputs under ignored
runtime/output directories, then mirror the final figure files into the figure
folder.

Example smoke run:

```powershell
python Fig5-lambda\run_fig5_lambda.py --requests 1000 --stop-pow
```

Paper-scale commands are documented in each figure folder README.

The runners restart PoW by default. To manage PoW manually, start it through:

```powershell
pow-4nodes-runtime\scripts\start-omnilink-pow-4nodes.ps1
```

and pass `--no-restart-pow` to the figure runner.

## Notes on Fig3, Fig4, Fig9, and Fig10

Fig3/Fig4 are Section VI.2 prototype/baseline figures. Their retained source
CSV files are kept under `Fig3/source_data` and `Fig4/source_data`. The older
temporary baseline-suite runner was not recovered, so these two figures are
reproducible from the retained measured summaries rather than from a full fresh
baseline execution.

Fig9/Fig10 are availability figures. Their retained source data are kept under
`Fig9/source_data` and `Fig10/source_data`. They use the same Fig7-style
service-time definition for DPKI and PKI.

## Git Hygiene

The `.gitignore` keeps the repository focused on reproducible sources and final
artifacts. It ignores:

- runtime logs, node databases, caches, output directories, and `node_modules`;
- recovered backups such as `oldver_simulation/` and `paper-figure-pipeline/`;
- local manuscript/rebuttal folders such as `JIoT/` and `response_letter/`.
- the legacy all-in-one `DPKI-and-DID-platform-Lenovo/` workspace, because the
  reproducible files have been consolidated into `dpki-experiment-prototype/`
  and `pow-4nodes-runtime/`.

Do not add ignored runtime directories back to Git unless they become required
inputs for a reproducible figure.
