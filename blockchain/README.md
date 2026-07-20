# Blockchain Runtime and Authentication Platforms

This directory contains all chain-facing components used by the experiments:

- `sidechain-three-chain/`: one main chain and two domain sidechains;
- `pow-4nodes-runtime/`: the retained four-node PoW launcher for compatibility checks;
- `dpki-experiment/`: shared real-system DPKI runner and canonical contract;
- `platforms/`: centralized PKI, proposed DPKI, Multi-CA DPKI, and full-contract DPKI modules;
- `platform_registry.js`: common platform registry used by the baseline experiment.

Public experiment entrypoints are under `../experiments/`. They initialize the
three-chain runtime automatically and archive logs from all three chains.
