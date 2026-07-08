# On-chain Cost Table

| Primitive | Applied request | Used by | On-chain storage B | Receipt gas used (10^3) |
| --- | --- | --- | --- | --- |
| Cert/root write | Management | Proposed Mgmt.; Multi-CA Mgmt.; full-contract Mgmt. | 654 | 181.3 |
| Auth record write + read | Intra-domain | Proposed DPKI (on-chain) | 590 | 216.5 |
| Auth record write + read | Cross-domain | Proposed DPKI (cross-domain) | 590 | 216.5 |
| Full-contract auth | Intra-domain | full-contract DPKI | 942 | 274.8 |
| Full-contract auth | Cross-domain | full-contract DPKI | 1006 | 279.5 |

All rows come from the latest one-group receipt-gas overhead run.
The table reports chain-side storage and final receipt gas used by the actually invoked write primitive.
Multi-CA internal committee coordination is excluded because it is not reflected as a chain-side primitive in the current prototype baseline.
