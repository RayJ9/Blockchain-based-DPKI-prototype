# Resource Overhead Table V3

## Management external payload

| Scheme | External payload B |
| --- | --- |
| Our proposed DPKI | 1615 |
| Centralized PKI | 1262 |
| Multi-CA based DPKI | 1674 |
| full-contract DPKI | 644 |

## Intra-domain authentication external payload

| Scheme | External payload B |
| --- | --- |
| Our proposed DPKI (off-chain) | 1585 |
| Our proposed DPKI (on-chain) | 2342 |
| Centralized PKI | 384 |
| Multi-CA based DPKI | 3286 |
| full-contract DPKI | 925 |

## Cross-domain authentication external payload

| Scheme | External payload B |
| --- | --- |
| Our proposed DPKI | 3925 |
| Centralized PKI | 1570 |
| Multi-CA based DPKI | 3740 |
| full-contract DPKI | 1298 |

## On-chain primitive cost summary

| Primitive | Used by | On-chain storage B | Gas (10^3) |
| --- | --- | --- | --- |
| Cert/root write | Proposed Mgmt.; Multi-CA Mgmt.; full-contract Mgmt. | 654 | 235.7 |
| Auth record write + read | Proposed Intra-on; Proposed Cross | 590 | 281.5 |
| Full-contract intra auth | full-contract Intra-on | 942 | 357.2 |
| Full-contract cross auth | full-contract Cross | 1006 | 363.3 |

All rows come from the latest one-group actual overhead run with stage-level payload breakdown.
The external payload panels compare management with management, intra-domain with intra-domain, and cross-domain with cross-domain.
Multi-CA internal committee coordination is intentionally excluded from the user-facing payload tables; its hidden coordination cost is kept only in the audit logs.
