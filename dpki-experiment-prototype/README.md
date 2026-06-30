# Chain33 DPKI Real Measurement

This folder runs the paper-style DPKI workflow against a real local Chain33 EVM node and records wall-clock request latency.

## What Is Real

- A local Chain33 node exposes Web3 RPC at `http://127.0.0.1:8545`.
- `DPKIExperiment.sol` is compiled with `solc@0.5.17` and deployed to Chain33 EVM.
- Certificate records, domain repository roots, and authentication records are written as real on-chain transactions.
- Off-chain DPKI authentication reads the on-chain repository root, verifies a local MPT-style hexary proof, verifies certificate signatures, and verifies an ECDSA authentication assertion.
- On-chain DPKI authentication verifies MPT proofs/signatures locally and writes an authentication record to the deployed Chain33 EVM contract, then reads it back.
- PKI authentication verifies real ECDSA certificate signatures through the hierarchical chain; cross-domain requests verify `Ea -> Sa -> Ga -> Gb`.
- `E[T]` is measured from request arrival wall-clock time to actual completion wall-clock time.

## Current Limits

- The request mix still follows the paper's configured proportions for `p`, `epsilon`, and `gamma`.
- The theory curves are still drawn from configured model parameters, not yet from parameters estimated from the real measurement trace.
- Chain33 transaction submission is serialized by default because this local Chain33 EVM setup reverted transactions under concurrent same-account submissions.

## Run

Start Chain33 EVM if it is not already running:

```powershell
.\scripts\start-chain33-evm.ps1
```

Run the measured experiment and regenerate the figures:

```powershell
node .\run-real-dpki-experiment.js --requests-per-epsilon 24
```

Stop the local Chain33 EVM node:

```powershell
.\scripts\stop-chain33-evm.ps1
```

## Outputs

- `outputs/real_simulation_results_by_epsilon.csv`
- `outputs/real_simulation_results_by_epsilon_detailed.csv`
- `outputs/real_summary_by_epsilon_detailed.csv`
- `outputs/lambda_summary_by_epsilon.csv`
- `outputs/Fig7_real_measured_ET.png`
- `..\..\simu2_tail_prob\simulation_results_by_epsilon.csv`
- `..\..\simu2_tail_prob\Fig7_epsilon_ET.png`
- `..\..\simu2_tail_prob\Fig7_real_measured_ET.png`
