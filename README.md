# Blockchain-Based DPKI Reproducible Experiment Package

This repository contains the source code and reproducible experiments for *Blockchain-Based Decentralized Public Key Infrastructure Modeling and Analysis*. It includes the lab-built Omnilink blockchain, a main-side chain deployment, four authentication platforms, real-system experiment runners, retained measurements, and the scripts used to produce the paper figures.

## 1. Environment

The experiment package is tested on 64-bit Windows with PowerShell 5.1. The following tools must be available on `PATH`:

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

For an existing compatible Omnilink build, `-SkipOmnilinkBuild` skips only the Go build. `-SkipPython` and `-SkipNode` skip their corresponding installation steps. All required commands must still be present on `PATH`.

The installation can be checked again at any time:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Check-Reproduction.ps1
```

## 2. Omnilink Blockchain

Omnilink is a lab-built blockchain system developed by our research group. It is implemented in Go and provides configurable PoW consensus, KV smart-contract support, and an EVM-compatible Solidity execution path. This repository contains the source needed to build the executable used by the experiments.

The experiment-facing interfaces are:

| Interface | Experiment use |
| --- | --- |
| Web3 JSON-RPC | chain ID and block queries, signed transaction submission, contract deployment/calls, and receipt retrieval |
| Chain JSON-RPC | chain-specific block and transaction observations used by the measurement backend |
| WebSocket and gRPC | interfaces exposed by each generated Omnilink node configuration |
| Health endpoint | startup and process-readiness checks |
| P2P port | isolated node/network communication |

The PoW launcher exposes `meanBlockMs`, `difficultyBits`, and empty-block mining as controlled inputs. Experiment scripts generate a TOML configuration for each node, start the processes, wait for RPC readiness, and archive the effective configurations and logs.


## 3. Authentication Schemes implements

All four implementations use the same host, cryptographic libraries, request driver, and blockchain configuration. The registry in `blockchain/platform_registry.js` exposes a common experiment interface while preserving the mechanism-specific workflow.

### Our proposed DPKI

`blockchain/platforms/proposed-dpki/` implements certificate management, intra-domain off-chain authentication, intra-domain on-chain authentication, and cross-domain authentication. It combines X.509 verification with MPT proof generation and verification. Management stores the complete certificate and repository state on chain. On-chain authentication additionally commits the authentication record and reads the recorded state. Cross-domain authentication checks the service-CA certificate state through the relayed MPT root. Each request includes its signed assertion exchange.

### Centralized PKI

`blockchain/platforms/centralized-pki/` is the conventional PKI baseline. It uses OpenSSL for key and CSR generation, certificate issuance, X.509 path verification, OCSP-style certificate-status validation, and signed assertions. It is an off-chain baseline and therefore deploys no contract. Cross-domain authentication performs the configured PKI trust-chain verification hops.

### Multi-CA based DPKI

`blockchain/platforms/multi-ca-dpki/` implements a 4-of-6 Multi-CA baseline. Six CA requests are issued concurrently, and authentication succeeds after four valid certificate/status responses. Management aggregates committee evidence and commits the certificate and validator evidence. The associated contract rejects duplicate validators and requires four distinct approvals.

### Full-contract DPKI

`blockchain/platforms/full-contract-dpki/` implements certificate management and authentication through a smart contract. Management stores CSR, certificate, status, and repository-root material. Authentication executes certificate/status and assertion checks, stores a validation digest, and writes the final audit result. The runner also performs the corresponding real OpenSSL certificate-path operation; it does not insert a fixed synthetic delay.

## 4. Experiments

Each directory below contains a `run_experiment.ps1` public entrypoint. The entrypoint starts the main chain and both sidechains, initializes their certificates and contracts, runs the selected workload, captures console and blockchain logs, and stops the processes on completion.

| Experiment directory | Function | Paper-scale requests |
| --- | --- | ---: |
|`experiments/pow-interval-validation/` | collects strict PoW inter-block samples and validates the block-interval distribution | 1,000 |
|`experiments/baseline-comparison/` | compares management, intra-domain, and cross-domain latency across the four platforms | 1,000 |
|`experiments/arrival-rate/` | sweeps request arrival rate and block rate for the response-time bounds and observations | 10,000 |
|`experiments/cross-domain-ratio/` | sweeps the cross-domain request ratio | 2,000 |
|`experiments/management-ratio/` | sweeps the certificate-management request ratio and compares DPKI with PKI | 2,000 |
|`experiments/service-ca-number/` | sweeps the number of service CAs | 10,000 |
|`experiments/availability-timeout/` | probes service-time tails and evaluates availability over failure probability and timeout threshold | 10,000 |
|`experiments/availability-service-ca-number/` | probes service-time tails and evaluates availability over failure probability and service-CA number | 10,000 |

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
only for the final MATLAB export. Existing retained data can be replotted
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
