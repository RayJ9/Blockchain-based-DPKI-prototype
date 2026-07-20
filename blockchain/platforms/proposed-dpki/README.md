# Our proposed DPKI platform

This module exports the management, intra-domain off-chain, intra-domain
on-chain, and cross-domain workflows used by `baseline-comparison`. The
parameter-sweep and availability experiments use the same `DPKIExperiment`
contract and shared real-prototype runtime.

The protocol stores complete certificates and MPT roots on chain. Off-chain
authentication verifies an X.509 certificate, obtains an MPT proof, and checks
the signed assertion. The measured MPT stage covers proof generation, the
on-chain root query, proof-signer verification, and Merkle-proof verification.
On-chain authentication additionally commits and reads the authentication
record. Cross-domain authentication verifies one additional MPT proof and
counts one end-to-end assertion.

`contracts/ProposedDPKI.sol` is the module-level contract entrypoint. It wraps
the canonical contract in `blockchain/dpki-experiment/contracts` so the paper
figures and this module cannot silently diverge.
