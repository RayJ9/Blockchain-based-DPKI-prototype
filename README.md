# Blockchain-Based DPKI Reproducible Experiment Package

This repository contains the source code and reproducible experiments for
*Blockchain-Based Decentralized Public Key Infrastructure Modeling and
Analysis*. It includes the lab-built Omnilink blockchain, a three-chain DPKI
deployment, four authentication platforms, real-system experiment runners,
retained measurements, and the scripts used to produce the paper figures.

New runs are written to isolated output directories. Existing figure files,
CSV data, MAT files, and other retained paper artifacts are not overwritten.

## 1. Environment

The experiment package is tested on 64-bit Windows with PowerShell 5.1. The
following tools must be available on `PATH`:

| Tool | Required version | Purpose |
| --- | --- | --- |
| PowerShell | 5.1 or newer | chain and experiment orchestration |
| Python | 3.10 or newer | workload generation, statistics, and data preparation |
| Node.js | 18 or newer | Web3, certificate, and smart-contract experiment runner |
| npm | supplied with Node.js | installs pinned Node.js packages |
| Go | 1.19 or newer | builds Omnilink from source |
| OpenSSL | 3.x | RSA keys, CSRs, X.509 certificates, signatures, and verification |
| MATLAB | R2024a recommended | optional final paper-figure export |
| Poppler | current release | optional PNG/PDF/EPS conversion for availability figures |

Python dependencies are declared in `requirements.txt`: NumPy, pandas, SciPy,
Matplotlib, Pillow, and their dependencies. The Node.js runner uses the pinned
`web3` and `solc` versions in `blockchain/dpki-experiment/package-lock.json`.

### Install

Clone the repository and run the setup script from its root:

```powershell
git clone https://github.com/RayJ9/Blockchain-based-DPKI-prototype.git
cd Blockchain-based-DPKI-prototype
powershell -ExecutionPolicy Bypass -File scripts\Setup-Environment.ps1
```

The setup script performs four operations:

1. Installs the Python packages from `requirements.txt`.
2. Runs `npm ci` in `blockchain/dpki-experiment`.
3. Builds `omni.exe` from the Go source under `omnilink/`.
4. Checks the platform modules, contracts, and public experiment entrypoints.

For an existing compatible Omnilink build, `-SkipOmnilinkBuild` skips only the
Go build. `-SkipPython` and `-SkipNode` skip their corresponding installation
steps. All required commands must still be present on `PATH`.

The installation can be checked again at any time:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Check-Reproduction.ps1
```

## 2. Omnilink Blockchain

Omnilink is a lab-built blockchain system developed by our research group. It
is implemented in Go and provides configurable PoW consensus, KV smart-contract
support, and an EVM-compatible Solidity execution path. This repository
contains the source needed to build the executable used by the experiments.

The experiment-facing interfaces are:

| Interface | Experiment use |
| --- | --- |
| Web3 JSON-RPC | chain ID and block queries, signed transaction submission, contract deployment/calls, and receipt retrieval |
| Chain JSON-RPC | chain-specific block and transaction observations used by the measurement backend |
| WebSocket and gRPC | interfaces exposed by each generated Omnilink node configuration |
| Health endpoint | startup and process-readiness checks |
| P2P port | isolated node/network communication |

The PoW launcher exposes `meanBlockMs`, `difficultyBits`, local miner count, and
empty-block mining as controlled inputs. Experiment scripts generate a TOML
configuration for each node, start the processes, wait for RPC readiness, and
archive the effective configurations and logs.

### Three-chain deployment

Every public experiment starts three independent Omnilink chains:

| Role | Chain ID | Web3 RPC | Stored state |
| --- | ---: | --- | --- |
| Main chain | 4100 | `http://127.0.0.1:18645` | service-CA registry and sidechain checkpoints |
| Sidechain A | 4101 | `http://127.0.0.1:18745` | Domain-A certificates, roots, and authentication records |
| Sidechain B | 4102 | `http://127.0.0.1:18845` | Domain-B certificates, roots, and authentication records |

`MainChainCARegistry.sol` registers service CAs and their latest sidechain
checkpoints. `SidechainDPKI.sol` manages certificate records and state roots
and records cross-domain authentication results. The launcher creates two real
OpenSSL certificate hierarchies, deploys the contracts, registers both CAs,
updates both sidechain roots, and relays the checkpoints to the main chain.

The checkpoint relay is an application-level implementation for the measured
DPKI workflow. It does not claim to be a trustless production bridge or a
cross-chain finality protocol.

A standalone three-chain check can be run with:

```powershell
.\blockchain\sidechain-three-chain\run_experiment.ps1
```

The retained four-node PoW launcher is located under
`blockchain/pow-4nodes-runtime/`. Public figure experiments use the three-chain
launcher automatically.

## 3. Authentication Platforms

All four implementations use the same host, cryptographic libraries, request
driver, and blockchain configuration. The registry in
`blockchain/platform_registry.js` exposes a common experiment interface while
preserving the mechanism-specific workflow.

### Our proposed DPKI

`blockchain/platforms/proposed-dpki/` implements certificate management,
intra-domain off-chain authentication, intra-domain on-chain authentication,
and cross-domain authentication. It combines X.509 verification with MPT proof
generation and verification. Management stores the complete certificate and
repository state on chain. On-chain authentication additionally commits the
authentication record and reads the recorded state. Cross-domain
authentication checks the service-CA certificate state through the relayed
MPT root. Each request includes its signed assertion exchange.

### Centralized PKI

`blockchain/platforms/centralized-pki/` is the conventional PKI baseline. It
uses OpenSSL for key and CSR generation, certificate issuance, X.509 path
verification, OCSP-style certificate-status validation, and signed
assertions. It is an off-chain baseline and therefore deploys no Solidity
contract. Cross-domain authentication performs the configured PKI trust-chain
verification hops.

### Multi-CA based DPKI

`blockchain/platforms/multi-ca-dpki/` implements a 4-of-6 Multi-CA baseline.
Six CA requests are issued concurrently, and authentication succeeds after
four valid certificate/status responses. Management aggregates committee
evidence and commits the certificate and validator evidence. The associated
contract rejects duplicate validators and requires four distinct approvals.

### Full-contract DPKI

`blockchain/platforms/full-contract-dpki/` implements certificate management
and authentication through a smart contract. Management stores CSR,
certificate, status, and repository-root material. Authentication executes
certificate/status and assertion checks, stores a validation digest, and
writes the final audit result. The runner also performs the corresponding real
OpenSSL certificate-path operation; it does not insert a fixed synthetic
delay.

## 4. Experiments

Each directory below contains a `run_experiment.ps1` public entrypoint. The
entrypoint starts the main chain and both sidechains, initializes their
certificates and contracts, runs the selected workload, captures console and
blockchain logs, and stops the processes on completion.

| Paper figure | Experiment directory | Function | Paper-scale requests |
| --- | --- | --- | ---: |
| Fig. 3 | `experiments/pow-interval-validation/` | collects strict PoW inter-block samples and validates the block-interval distribution | 1,000 |
| Fig. 4 | `experiments/baseline-comparison/` | compares management, intra-domain, and cross-domain latency across the four platforms | 1,000 |
| Fig. 5 | `experiments/arrival-rate/` | sweeps request arrival rate and block rate for the response-time bounds and observations | 10,000 |
| Fig. 6 | `experiments/cross-domain-ratio/` | sweeps the cross-domain request ratio | 2,000 |
| Fig. 7 | `experiments/management-ratio/` | sweeps the certificate-management request ratio and compares DPKI with PKI | 2,000 |
| Fig. 8 | `experiments/service-ca-number/` | sweeps the number of service CAs | 10,000 |
| Fig. 9 | `experiments/availability-timeout/` | probes service-time tails and evaluates availability over failure probability and timeout threshold | 10,000 |
| Fig. 10 | `experiments/availability-service-ca-number/` | probes service-time tails and evaluates availability over failure probability and service-CA number | 10,000 |

### Run one experiment

Use a small request count for a quick real-chain check:

```powershell
experiments\pow-interval-validation\run_experiment.ps1 -SampleCount 100
experiments\baseline-comparison\run_experiment.ps1 -Requests 50
experiments\arrival-rate\run_experiment.ps1 -Requests 50
experiments\cross-domain-ratio\run_experiment.ps1 -Requests 50
experiments\management-ratio\run_experiment.ps1 -Requests 50
experiments\service-ca-number\run_experiment.ps1 -Requests 50
experiments\availability-timeout\run_experiment.ps1 -Requests 50
experiments\availability-service-ca-number\run_experiment.ps1 -Requests 50
```

Use `-PaperScale` to select the paper grid and request count for that
experiment. During execution, the terminal prints generated certificate
information, PEM content, transaction hashes, receipt status, block numbers,
contract operations, and per-stage request measurements.

Run a minimal session for all figures with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Run-All-Smoke.ps1 -Requests 10
```

Fig. 4 reports latency and latency distributions. Raw receipts remain in the
logs for reproducibility, but communication, storage, and gas are not
aggregated as comparison metrics. Fig. 9 and Fig. 10 execute a real-chain tail
probe and preserve the paper's retained availability surfaces separately.

### Results and logs

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

The same session is compressed to:

```text
experiment_archives/experiment-name_YYYYMMDD_HHMMSS.zip
```

The archive contains the console transcript, generated chain configurations,
logs from all three chains, transaction and receipt records, request samples,
certificate artifacts, and the run manifest. Runtime databases are excluded
because they are large and are regenerated by the launcher.

### Replot retained figures

MATLAB is not required to execute the blockchain experiments. It is needed
only for the final MATLAB paper export. Existing retained data can be replotted
without rerunning the experiments:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Replot-Retained-Figures.ps1
```

## 5. Repository Layout

| Path | Contents |
| --- | --- |
| `omnilink/` | complete Omnilink Go source and PoW configuration template |
| `blockchain/sidechain-three-chain/` | main-chain and two-sidechain runtime, contracts, and initialization workflow |
| `blockchain/pow-4nodes-runtime/` | retained four-node PoW compatibility launcher |
| `blockchain/dpki-experiment/` | shared Node.js real-system runner and canonical DPKI contract |
| `blockchain/platforms/` | proposed DPKI and three comparison platforms |
| `blockchain/.internal/old-ver-simulations/` | old-version compatibility modules still imported by Fig. 5-Fig. 10 runners |
| `figure_dpki_pki_runtime/` | shared sweep, measurement, and availability-statistics code |
| `experiments/` | semantic experiment entrypoints, retained measurements, and figure scripts |
| `scripts/` | installation, checking, orchestration, tail extraction, and artifact archiving |

The old-version compatibility directory is internal implementation support;
users should start experiments only through `experiments/*/run_experiment.ps1`.
Local manuscript and response-letter material is excluded from the GitHub
package.
