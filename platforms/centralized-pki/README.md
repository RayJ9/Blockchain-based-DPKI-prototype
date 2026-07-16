# Centralized PKI platform

This module implements certificate issuance, X.509 chain verification, OCSP
status validation, and signed assertions. It is intentionally off-chain and
therefore has no Solidity deployment. The executable workflow is exported by
`index.js` and is used by the `baseline-comparison` experiment.

Request classes:

- `management`: key/CSR generation, certificate issuance, and two signed
  request/reply assertions.
- `intra-auth`: one certificate verification, one OCSP check, and one
  assertion exchange.
- `cross-auth`: four PKI trust-chain verification hops.

The runtime generates its OpenSSL keys, CSRs, certificates, public keys, and
OCSP status files inside the selected experiment artifact directory.
