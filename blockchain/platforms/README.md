# Authentication Platforms

The four platform modules share the same experiment runtime and blockchain
configuration so their results can be compared under controlled conditions.

- `proposed-dpki/`: proposed MPT-based DPKI.
- `centralized-pki/`: centralized X.509 and OCSP baseline.
- `multi-ca-dpki/`: 4-of-6 multi-CA baseline.
- `full-contract-dpki/`: full smart-contract execution baseline.

`../platform_registry.js` exposes these modules to the
baseline-comparison runner without changing the mechanism identifiers stored
in retained measurement data.
