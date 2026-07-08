# Resource Overhead Table V2

| Mechanism | Request | External payload B | On-chain storage B | Gas (10^3) | Internal coordination B |
| --- | --- | --- | --- | --- | --- |
| Our proposed DPKI | Mgmt. | 1615 | 654 | 235.7 | - |
| Our proposed DPKI | Intra-off | 1585 | - | - | - |
| Our proposed DPKI | Intra-on | 2342 | 590 | 281.5 | - |
| Our proposed DPKI | Cross | 3925 | 590 | 281.5 | - |
| Centralized PKI | Mgmt. | 1262 | - | - | - |
| Centralized PKI | Intra | 384 | - | - | - |
| Centralized PKI | Cross | 1570 | - | - | - |
| Multi-CA based DPKI | Mgmt. | 1674 | 654 | 235.7 | 62092 |
| Multi-CA based DPKI | Intra | 3286 | - | - | - |
| Multi-CA based DPKI | Cross | 3740 | - | - | - |
| full-contract DPKI | Mgmt. | 644 | 654 | 235.7 | - |
| full-contract DPKI | Intra-on | 925 | 942 | 357.2 | - |
| full-contract DPKI | Cross | 1298 | 1006 | 363.3 | - |

All rows come from the latest one-group actual overhead run with stage-level payload breakdown.
External payload counts only externally transmitted protocol bytes.
Internal coordination is reported only for Multi-CA based DPKI and is separated from the user-facing payload columns.
