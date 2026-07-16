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
| Centralized PKI | `platforms/centralized-pki/` | X.509 verification, OCSP, signed assertion |
| Our proposed DPKI | `platforms/proposed-dpki/` | X.509, MPT proof, optional on-chain authentication record |
| Multi-CA based DPKI | `platforms/multi-ca-dpki/` | 4-of-6 CA responses and threshold evidence |
| Full contract DPKI | `platforms/full-contract-dpki/` | certificate/status/assertion checks and result storage in a contract |

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
- Poppler (`pdftops`) for the retained availability-timeout conversion path

Install dependencies and build Omnilink:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Setup-Environment.ps1
```

The command installs `requirements.txt`, runs `npm ci` in
`dpki-experiment-prototype`, builds the four-node Omnilink runtime, and checks
all public entrypoints. Use `-SkipOmnilinkBuild` when a compatible binary is
already present.

## Run an experiment

Every runnable experiment has a `run_experiment.ps1` entrypoint. A short real-chain run is:

```powershell
experiments\baseline-comparison\run_experiment.ps1 -Requests 50
experiments\arrival-rate\run_experiment.ps1 -Requests 50
experiments\cross-domain-ratio\run_experiment.ps1 -Requests 50
experiments\management-ratio\run_experiment.ps1 -Requests 50
experiments\service-ca-number\run_experiment.ps1 -Requests 50
experiments\availability-timeout\run_experiment.ps1 -Requests 50
experiments\availability-service-ca-number\run_experiment.ps1 -Requests 50
```

Add `-PaperScale` to use the paper sweep grid and request count for that
experiment. The baseline and parameter-sweep experiments execute the actual OpenSSL,
MPT, HTTP/OCSP, smart-contract, and Omnilink PoW paths. The two availability
experiments execute a lightweight real-chain probe
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
  experiment-name/
    experiment-name_YYYYMMDD_HHMMSS/
      console.log
      results/
      blockchain_logs/
      prototype_run_logs/
      artifact_manifest.json
```

The complete session is also written to one archive:

```text
experiment_archives/experiment-name_YYYYMMDD_HHMMSS.zip
```

The archive contains the console transcript, Omnilink node logs/configuration,
receipt and transaction breakdowns, detailed request samples, certificate
artifacts where produced, and the experiment manifest. Runtime databases are
excluded because they are large and are reconstructed by the launcher.

## Figure-specific reproduction

| Figure | Folder | Real experiment path |
| --- | --- | --- |
| Fig. 3 | `experiments/pow-interval-validation/` | PoW interval-distribution validation |
| Fig. 4 | `experiments/baseline-comparison/` | mixed execution of all four platforms |
| Fig. 5 | `experiments/arrival-rate/` | arrival-rate and block-rate sweep |
| Fig. 6 | `experiments/cross-domain-ratio/` | cross-domain-request-ratio sweep |
| Fig. 7 | `experiments/management-ratio/` | management-request-ratio sweep |
| Fig. 8 | `experiments/service-ca-number/` | service-CA-number sweep |
| Fig. 9 | `experiments/availability-timeout/` | availability over failure probability and timeout threshold |
| Fig. 10 | `experiments/availability-service-ca-number/` | availability over failure probability and service-CA number |

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

## Optional three-chain sidechain prototype

An isolated multi-ledger prototype is available under
`sidechain-three-chain-prototype/`. It starts one main chain and two domain
sidechains with separate EVM chain IDs, ports, databases, contracts, and logs.
The main chain stores CA records and relayed sidechain checkpoints; each
sidechain stores its own certificate state and authentication records.

```powershell
.\sidechain-three-chain-prototype\run_experiment.ps1
```

The smoke test generates real X.509 certificates, deploys all three contracts,
relays both sidechain roots, and records a verified Sidechain-A to Sidechain-B
authentication. This is an application-level checkpoint prototype rather than
a trustless production bridge; the distinction and security limitations are
documented in the module README.

## Repository layout

- `omnilink/`: Omnilink source.
- `pow-4nodes-runtime/`: four-node PoW build/start/stop scripts.
- `dpki-experiment-prototype/`: canonical DPKI contract and real experiment.
- `figure_dpki_pki_runtime/`: shared parameter-sweep and availability measurement/statistics code.
- `simu2-8-packaged/`: queueing-model and real-sweep bridge.
- `experiments/`: semantically named launch, retained result, and plotting folders.
- `platforms/`: four platform implementations and contract assets.
- `sidechain-three-chain-prototype/`: isolated main-chain/two-sidechain prototype.
- `scripts/`: setup, checking, orchestration, tail extraction, and archiving.

`JIoT/` and `response_letter/` are intentionally ignored and are not part of
the GitHub package.
