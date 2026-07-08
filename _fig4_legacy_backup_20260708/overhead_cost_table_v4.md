# Resource Overhead Table V4

## Management comparison

| Scheme | External payload B | On-chain storage B | Gas (10^3) |
| --- | --- | --- | --- |
| Our proposed DPKI | 1616 | 654 | 181.3 |
| Centralized PKI | 1258 | - | - |
| Multi-CA based DPKI | 1676 | 654 | 181.3 |
| full-contract DPKI | 645 | 654 | 181.3 |

## Intra-domain authentication comparison

| Scheme | External payload B | On-chain storage B | Gas (10^3) |
| --- | --- | --- | --- |
| Our proposed DPKI (off-chain) | 1586 | - | - |
| Our proposed DPKI (on-chain) | 2341 | 590 | 216.5 |
| Centralized PKI | 385 | - | - |
| Multi-CA based DPKI | 3286 | - | - |
| full-contract DPKI | 925 | 942 | 274.8 |

## Cross-domain authentication comparison

| Scheme | External payload B | On-chain storage B | Gas (10^3) |
| --- | --- | --- | --- |
| Our proposed DPKI | 3923 | 590 | 216.5 |
| Centralized PKI | 1573 | - | - |
| Multi-CA based DPKI | 3740 | - | - |
| full-contract DPKI | 1298 | 1006 | 279.5 |

All rows come from the latest one-group actual overhead run with stage-level payload breakdown.
Each panel compares the same request type across mechanisms and reports both external payload and on-chain cost inline.
Multi-CA internal committee coordination is intentionally excluded from these user-facing comparisons and kept only in the audit logs.
Repeated on-chain values indicate that the corresponding schemes invoke the same chain-side write primitive under that request type.
