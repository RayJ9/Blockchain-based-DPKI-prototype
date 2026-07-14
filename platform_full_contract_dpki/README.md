# Full smart-contract DPKI platform

This module models certificate issuance/state initialization and authentication
inside a smart contract. Management stores CSR, X.509 certificate, status data,
and the repository root. Authentication verifies certificate status and the
service assertion in the contract and writes the final authentication record.

The executable JavaScript workflow is exported by `index.js` and is exercised
by the Fig4 mixed benchmark. `contracts/FullContractDPKI.sol` is the module-level
deployment entrypoint.
