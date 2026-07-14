# Our proposed DPKI platform

This module exports the management, intra-domain off-chain, intra-domain
on-chain, and cross-domain workflows used by Fig4. Fig5-Fig10 use the same
`DPKIExperiment` contract and the shared real-prototype runtime.

The protocol stores complete certificates and MPT roots on chain. Off-chain
authentication verifies an X.509 certificate, obtains an MPT proof, and checks
the signed assertion. On-chain authentication additionally commits and reads
the authentication record.

`contracts/ProposedDPKI.sol` is the module-level contract entrypoint. It wraps
the canonical contract in `dpki-experiment-prototype/contracts` so the paper
figures and this module cannot silently diverge.
