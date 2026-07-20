# Blockchain-Based DPKI Reproducible Experiment Package

This repository provides the executable platforms, experiment runners,
retained measurements, and plotting code for *Blockchain-Based Decentralized
Public Key Infrastructure Modeling and Analysis*. It is organized as a
reproducible system package: each experiment has one public launcher, every new
run is isolated from retained paper data, and blockchain logs are archived with
the corresponding measurements.

## Omnilink blockchain runtime

Omnilink is a lab-built blockchain system developed by our research group. In
this project, it provides the common ledger and smart-contract environment for
the proposed DPKI platform and blockchain-based baselines. The experiment build
uses a configurable PoW consensus implementation, independent node data
directories, EVM-compatible contract execution, transaction receipts, and KV
state storage. Its block interval and mining difficulty can be controlled by
the launchers for the experiments in Section VI.

The public repository distributes Omnilink as a verified Windows x64 binary
package under `omnilink-runtime/`; the Omnilink source tree is not needed to run
the experiments. On first use, the launcher checks the archive size and
SHA-256 digest, extracts `omni.exe`, verifies the executable again, and then
starts the requested nodes.

The four-node runtime exposes the following interfaces by default:

| Interface | Node 0 | Purpose |
| --- | --- | --- |
| Web3 JSON-RPC | `http://127.0.0.1:8545` | EVM deployment, contract calls, transactions, and receipts |
| Chain JSON-RPC | `http://127.0.0.1:8801` | Native Omnilink chain queries and administration |
| gRPC | `127.0.0.1:8802` | Native typed RPC interface |
| WebSocket | `ws://127.0.0.1:8546` | EVM-compatible event and subscription access |
| Health | `http://127.0.0.1:8805` | Node health and synchronization checks |
| P2P | `127.0.0.1:13803` | Block and transaction propagation |

Nodes 1-3 use the same interface layout with increments of 10 for RPC ports
and increments of 1 for P2P ports. The generated configurations, process logs,
and databases are kept under `pow-4nodes-runtime/runtime/`. Runtime databases
are reconstructed for each clean run and are not versioned.

Install or verify only the Omnilink runtime with:

```powershell
.\omnilink-runtime\Install-OmnilinkRuntime.ps1
.\omnilink-runtime\Install-OmnilinkRuntime.ps1 -VerifyOnly
```

## Authentication platforms

All four platforms use the same workstation, OpenSSL/X.509 implementation,
request workload, and, when applicable, Omnilink configuration. This keeps the
underlying blockchain and cryptographic environment fixed while changing the
authentication design.

### Our proposed DPKI

`platforms/proposed-dpki/` implements certificate management and three
authentication paths:

- intra-domain off-chain authentication verifies an entity certificate, its
  MPT status proof, and the signed assertion;
- intra-domain on-chain authentication additionally commits the
  authentication record and resolves the recorded state;
- cross-domain authentication verifies the entity certificate and the remote
  service-CA state through an additional MPT proof before resolving the
  on-chain authentication record.

The module contains the platform adapter and `ProposedDPKI.sol`; the canonical
experiment contract remains in `dpki-experiment-prototype/contracts/`.

### Centralized PKI baseline

`platforms/centralized-pki/` uses OpenSSL X.509 certificate issuance and chain
verification, an OCSP status service, and signed assertions. It provides
management, intra-domain authentication, and a multi-segment cross-domain PKI
workflow without blockchain state.

### Multi-CA based DPKI baseline

`platforms/multi-ca-dpki/` implements a 4-of-6 policy. Six CA workers process
requests concurrently, and authentication succeeds after four valid responses
have been collected. The module covers distributed certificate management,
intra-domain validation, cross-domain validation, threshold evidence, and the
corresponding chain record where required. Its contract entrypoint is
`ThresholdValidationDPKI.sol`.

### Full contract DPKI baseline

`platforms/full-contract-dpki/` places certificate/status checking and result
recording in one smart-contract workflow. Management, intra-domain
authentication, and cross-domain authentication return real transaction
receipts after contract execution. The implementation is defined by
`FullContractDPKI.sol` and its platform adapter.

Machine-readable definitions for all platforms are stored in each
`platform.json`. The shared registry is `platform_registry.js`.

## Prerequisites

The tested environment is 64-bit Windows with PowerShell 5.1 or newer. Install:

- Python 3.10 or newer;
- Node.js 18 or newer and npm;
- OpenSSL 3.x;
- MATLAB for regenerating final MATLAB paper figures;
- Poppler (`pdftops`) for the retained Fig. 9 conversion path.

Go is not required because the verified Omnilink binary is included. Install
Python and Node.js dependencies, extract Omnilink, and check public entrypoints:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Setup-Environment.ps1
```

`-SkipPython`, `-SkipNode`, and `-SkipOmnilinkInstall` can be used when the
corresponding environment is already prepared.

## Experiments

Every experiment directory has a `run_experiment.ps1` entrypoint. New results
are written under `experiment_artifacts/`; retained CSV, MAT, EPS, PDF, and PNG
paper artifacts are never overwritten by an experiment run.

| Paper figure | Experiment | Function |
| --- | --- | --- |
| Fig. 3 | `experiments/pow-interval-validation/` | Validates the strict Omnilink PoW clock against an exponential inter-block distribution and reports the fitted mining-rate parameter. |
| Fig. 4 | `experiments/baseline-comparison/` | Executes mixed requests for the proposed DPKI, centralized PKI, Multi-CA DPKI, and full contract DPKI, and reports stage and total latency statistics. |
| Fig. 5 | `experiments/arrival-rate/` | Sweeps authentication request arrival rate and PoW block rate to evaluate response-time bounds and experimental response time. |
| Fig. 6 | `experiments/cross-domain-ratio/` | Changes the fraction of cross-domain authentication requests while keeping the remaining workload definition fixed. |
| Fig. 7 | `experiments/management-ratio/` | Changes the fraction of certificate-management requests and compares DPKI and PKI response time. |
| Fig. 8 | `experiments/service-ca-number/` | Changes service-CA number `m` and measures its effect on DPKI and PKI response time. |
| Fig. 9 | `experiments/availability-timeout/` | Runs a real-chain latency probe, extracts p90/p95/p99 and timeout-tail samples, and evaluates availability over failure probability and timeout threshold. |
| Fig. 10 | `experiments/availability-service-ca-number/` | Runs a real-chain probe for a selected service-CA count, extracts tail samples, and evaluates availability over failure probability and `m`. |

Run a short real experiment directly:

```powershell
.\experiments\pow-interval-validation\run_experiment.ps1 -SampleCount 100
.\experiments\baseline-comparison\run_experiment.ps1 -Requests 50
.\experiments\arrival-rate\run_experiment.ps1 -Requests 50
.\experiments\cross-domain-ratio\run_experiment.ps1 -Requests 50
.\experiments\management-ratio\run_experiment.ps1 -Requests 50
.\experiments\service-ca-number\run_experiment.ps1 -Requests 50
.\experiments\availability-timeout\run_experiment.ps1 -Requests 50
.\experiments\availability-service-ca-number\run_experiment.ps1 -Requests 50
```

Or use the central launcher:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Run-FigureExperiment.ps1 -Figure 4 -Requests 50
powershell -ExecutionPolicy Bypass -File scripts\Run-All-Smoke.ps1 -Requests 10
```

Add `-PaperScale` to the central launcher to use the retained paper sweep grid
and request count for a selected experiment. These runs can take substantially
longer than a smoke test.

During execution, the terminal prints certificate material, certificate
status, MPT evidence, transaction hashes, block numbers, contract receipts,
and per-stage measurements. Detailed traces are enabled by the central
launcher through `DPKI_VERBOSE_TRACE` and `DPKI_LIVE_TRACE`.

## Results and blockchain logs

Each run creates an isolated session:

```text
experiment_artifacts/
  experiment-name/
    experiment-name_YYYYMMDD_HHMMSS/
      console.log
      console_full.log
      command_logs/
      results/
      blockchain_logs/
      prototype_run_logs/
      artifact_manifest.json
```

The artifact collector also creates:

```text
experiment_archives/experiment-name_YYYYMMDD_HHMMSS.zip
```

The archive includes the console transcript, generated node configurations,
Omnilink logs, transaction and receipt traces, certificate artifacts, detailed
request samples, and the experiment manifest. Large runtime databases are not
included because the clean launcher reconstructs them.

Run structural and dependency checks at any time:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Check-Reproduction.ps1
```

Regenerate figures from retained final data without running experiments:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Replot-Retained-Figures.ps1
```

## Optional three-chain prototype

`sidechain-three-chain-prototype/` starts one main chain and two domain
sidechains from the same Omnilink binary. The three chains use separate EVM
chain IDs, RPC ports, databases, contracts, and logs. The main chain maintains
CA records and relayed sidechain checkpoints, while each sidechain maintains
its local certificate and authentication state.

```powershell
.\sidechain-three-chain-prototype\run_experiment.ps1
```

This module is an application-level checkpoint prototype rather than a
trustless production bridge; its security scope is documented in the module
README.

## Repository layout

- `omnilink-runtime/`: verified precompiled Omnilink runtime and PoW template;
- `pow-4nodes-runtime/`: four-node start, stop, configuration, and log scripts;
- `platforms/`: adapters, metadata, and contracts for the four platforms;
- `dpki-experiment-prototype/`: canonical DPKI contract and real workflow;
- `figure_dpki_pki_runtime/`: shared measurement and statistics code;
- `simu2-8-packaged/`: queueing-model and real-sweep bridge;
- `experiments/`: launchers, retained measurements, and plotting code;
- `sidechain-three-chain-prototype/`: isolated main-chain/two-sidechain test;
- `scripts/`: setup, integrity checks, orchestration, and artifact collection.

`JIoT/`, `response_letter/`, and private research backups are intentionally
excluded from the GitHub package.
