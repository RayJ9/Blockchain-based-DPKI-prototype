# DPKI Real-System Runner

This directory contains the shared Node.js runner and canonical DPKI contract
used by the parameter-sweep experiments. It connects to the Sidechain A Web3
and JSON-RPC endpoints supplied by the public PowerShell launcher.

The runner executes real OpenSSL/X.509 operations, MPT proof generation and
verification, OCSP-style status queries, signed assertions, smart-contract
transactions, and receipt/state reads. Raw outputs are written under
`outputs/`; public experiment launchers redirect and archive each run under
the root `experiment_artifacts/` directory.

Install dependencies from the repository root with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Setup-Environment.ps1
```

Normal users should start workloads through `experiments/*/run_experiment.ps1`
so the main chain, both sidechains, CA registry, logs, and cleanup are handled
consistently.
