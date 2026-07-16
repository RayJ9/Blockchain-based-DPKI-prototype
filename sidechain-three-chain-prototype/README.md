# Three-Chain Sidechain Prototype

This optional prototype runs three independent Omnilink PoW chains on one workstation. It does not modify or share the runtime used by the experiments under `experiments/`.

## Architecture

| Role | EVM chain ID | Web3 RPC | Stored state |
|---|---:|---|---|
| Main chain | 4100 | `http://127.0.0.1:18645` | CA registry and latest sidechain checkpoints |
| Sidechain A | 4101 | `http://127.0.0.1:18745` | Domain-A certificates, certificate state root, authentication records |
| Sidechain B | 4102 | `http://127.0.0.1:18845` | Domain-B certificates, certificate state root, authentication records |

`MainChainCARegistry.sol` registers the CA that governs each sidechain and stores relayed checkpoints. `SidechainDPKI.sol` issues and revokes certificate records, maintains the current state root, and records cross-domain authentication results.

The relay is deliberately application-level: the runner reads a sidechain root and submits it to the main-chain registry. This validates the deployment and DPKI workflow without claiming a trustless bridge, cross-chain consensus, or finality proof.

## Run

Install the root project environment first, then run:

```powershell
.\sidechain-three-chain-prototype\run_experiment.ps1
```

The experiment performs the following real operations:

1. Starts three isolated Omnilink instances with separate databases and ports.
2. Generates two OpenSSL X.509 CA/leaf hierarchies.
3. Deploys the main-chain registry and one DPKI contract on each sidechain.
4. Registers both CAs on the main chain.
5. Issues certificates and updates state roots on both sidechains.
6. Relays both roots to the main chain.
7. Verifies a Sidechain-A certificate through the main-chain checkpoint and records the accepted result on Sidechain B.

The terminal prints the certificates, transaction hashes, receipts, gas use, block heights, relay messages, and final verification. Outputs are isolated under `outputs/`; all three chain logs and configurations are copied into the session and compressed under `archives/`.

Use `-KeepChains` to leave the three nodes running after the smoke test. Stop them with:

```powershell
.\sidechain-three-chain-prototype\scripts\stop-three-chains.ps1
```

## Scope

This is a multi-ledger prototype, not a production sidechain bridge. A production design must additionally define checkpoint authorization, replay protection, challenge/finality rules, validator rotation, and fault handling for a dishonest relay.
