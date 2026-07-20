# Experiments

Experiment directories use their measured variable or evaluation objective
rather than a paper figure number. Paper numbering is retained only as a
cross-reference.

| Paper figure | Directory | Evaluation |
| --- | --- | --- |
| Fig. 3 | `pow-interval-validation/` | PoW interval-distribution validation |
| Fig. 4 | `baseline-comparison/` | latency comparison of four platforms |
| Fig. 5 | `arrival-rate/` | request-arrival-rate sweep |
| Fig. 6 | `cross-domain-ratio/` | cross-domain-request-ratio sweep |
| Fig. 7 | `management-ratio/` | certificate-management-request-ratio sweep |
| Fig. 8 | `service-ca-number/` | service-CA-number sweep |
| Fig. 9 | `availability-timeout/` | availability over failure probability and timeout threshold |
| Fig. 10 | `availability-service-ca-number/` | availability over failure probability and service-CA number |

Each runnable directory exposes `run_experiment.ps1`. Retained figure inputs
and outputs stay inside the owning experiment directory, while new run logs and
receipts are written under `experiment_artifacts/<experiment-name>/`.
