# Full smart-contract DPKI platform

This module models certificate issuance/state initialization and authentication
inside a smart contract. Management stores CSR, X.509 certificate, status data,
and the repository root. Authentication verifies certificate status and the
service assertion in the contract and writes the final authentication record.
The benchmark also performs actual OpenSSL certificate-path validation and
reads and inspects complete on-chain CSR, certificate, and status material.
The contract verifies the assertion signature, records the validation digest,
and stores the authentication audit result. These operations provide the
measured execution cost; the runner does not inject a fixed delay.

The executable JavaScript workflow is exported by `index.js` and is exercised
by the `baseline-comparison` experiment. `contracts/FullContractDPKI.sol` is the module-level
deployment entrypoint.
