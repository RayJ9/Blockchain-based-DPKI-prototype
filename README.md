# Blockchain-Based DPKI Reproducible Experiment Package

This repository contains the Omnilink PoW blockchain, OpenSSL/X.509 services,
four authentication platforms, experiment runners, retained measurements, and
paper-figure scripts for *Blockchain-Based Decentralized Public Key
Infrastructure Modeling and Analysis*.

The current `figure.*`, retained CSV, MAT, and plotting inputs are versioned
paper artifacts. New experiments are isolated under `experiment_artifacts/`
and never overwrite those files.

## Implemented platforms

| Platform | Module | Authentication mechanism |
| --- | --- | --- |
| Centralized PKI | `platform_traditional_pki/` | X.509 verification, OCSP, signed assertion |
| Our proposed DPKI | `platform_proposed_dpki/` | X.509, MPT proof, optional on-chain authentication record |
| Multi-CA based DPKI | `platform_threshold_dpki/` | 4-of-6 CA responses and threshold evidence |
| Full contract DPKI | `platform_full_contract_dpki/` | certificate/status/assertion checks and result storage in a contract |

Each module contains its executable workflow, a machine-readable
`platform.json`, documentation, and its contract entrypoint or an explicit
explanation of why no contract is used.

## Prerequisites

The tested host is Windows with PowerShell 5.1 or newer. Install:

- Python 3.10+
- Node.js 18+ and npm
- Go
- OpenSSL 3.x
- MATLAB for the final MATLAB paper exports
- Poppler (`pdftops`) for the retained Fig9 conversion path

Install dependencies and build Omnilink:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Setup-Environment.ps1
```

The command installs `requirements.txt`, runs `npm ci` in
`dpki-experiment-prototype`, builds the four-node Omnilink runtime, and checks
all public entrypoints. Use `-SkipOmnilinkBuild` when a compatible binary is
already present.

## Run an experiment

Every figure has a `run_experiment.ps1` entrypoint. A short real-chain run is:

```powershell
Fig4\run_experiment.ps1 -Requests 50
Fig5-lambda\run_experiment.ps1 -Requests 50
Fig6-epsilon\run_experiment.ps1 -Requests 50
Fig7-p\run_experiment.ps1 -Requests 50
Fig8-M\run_experiment.ps1 -Requests 50
Fig9\run_experiment.ps1 -Requests 50
Fig10\run_experiment.ps1 -Requests 50
```

Add `-PaperScale` to use the paper sweep grid and request count for that
figure. Fig4-Fig8 execute the actual OpenSSL, MPT, HTTP/OCSP, smart-contract,
and Omnilink PoW paths. Fig9 and Fig10 execute a lightweight real-chain probe
and extract observed p90/p95/p99 and timeout-tail data; the retained 3D/2D
surface inputs remain unchanged.

During a run, the console prints certificate records, transaction hashes,
block numbers, receipt status, gas usage, stage statistics, and per-request
details. Set by the launcher, `DPKI_VERBOSE_TRACE=1` controls the detailed Node
trace and `DPKI_LIVE_TRACE=1` tees the prototype log to the console.

## Results and logs

Each run creates an isolated session:

```text
experiment_artifacts/
  FigX/
    FigX_YYYYMMDD_HHMMSS/
      console.log
      results/
      blockchain_logs/
      prototype_run_logs/
      artifact_manifest.json
```

The complete session is also written to one archive:

```text
experiment_archives/FigX_YYYYMMDD_HHMMSS.zip
```

The archive contains the console transcript, Omnilink node logs/configuration,
receipt and transaction breakdowns, detailed request samples, certificate
artifacts where produced, and the experiment manifest. Runtime databases are
excluded because they are large and are reconstructed by the launcher.

## Figure-specific reproduction

| Figure | Folder | Real experiment path |
| --- | --- | --- |
| Fig4 | `Fig4/` | mixed execution of all four platforms |
| Fig5 | `Fig5-lambda/` | arrival-rate and block-rate sweep |
| Fig6 | `Fig6-epsilon/` | queueing-threshold sweep |
| Fig7 | `Fig7-p/` | management-request-ratio sweep |
| Fig8 | `Fig8-M/` | service-node-count sweep |
| Fig9 | `Fig9/` | real Fig7-style probe plus latency-tail extraction |
| Fig10 | `Fig10/` | real Fig8-style probe plus latency-tail extraction |

The original Python entrypoints remain available for custom grids. Replotting
the retained final artifacts is separate:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Replot-Retained-Figures.ps1
```

Run the source and dependency integrity check at any time:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Check-Reproduction.ps1
```

Run a minimal real-chain session for every figure:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Run-All-Smoke.ps1 -Requests 10
```

## Repository layout

- `omnilink/`: Omnilink source.
- `pow-4nodes-runtime/`: four-node PoW build/start/stop scripts.
- `dpki-experiment-prototype/`: canonical DPKI contract and real experiment.
- `figure_dpki_pki_runtime/`: shared Fig5-Fig10 measurement/statistics code.
- `simu2-8-packaged/`: queueing-model and real-sweep bridge.
- `Fig4/`-`Fig10/`: figure-owned launch, retained result, and plotting files.
- `platform_*/`: four platform implementations and contract assets.
- `scripts/`: setup, checking, orchestration, tail extraction, and archiving.

`JIoT/` and `response_letter/` are intentionally ignored and are not part of
the GitHub package.
