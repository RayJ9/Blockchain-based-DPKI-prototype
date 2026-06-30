# Performance Summary Tables

This folder builds paper-ready performance tables from saved measurement
outputs. It does not run the blockchain prototype and does not regenerate any
figures.

Default inputs:

- `../service_probe/*/detailed_requests.csv`
- `../service_probe/combined_distribution_check.csv`
- `../real_chain_tx_breakdown.csv`

Run after the measurement files already exist:

```powershell
python .\simu2_tail_prob\performance_summary\build_performance_tables.py
```

Outputs are written to `result/`:

- `workflow_latency_table.csv`: end-to-end latency by workflow.
- `stage_cost_table.csv`: fine-grained operation costs parsed from
  `stageTimingsJson`.
- `chain_transaction_cost_table.csv`: smart-contract transaction latency and
  gas usage by method.
- `practical_costs_table.csv`: compact table aligned with reviewer-requested
  practical costs.
- `practical_costs_table.md`: Markdown version for manuscript drafting.
- `metric_summary.json`: machine-readable summary and source paths.

Interpretation notes:

- `gasUsed` is reported as the on-chain storage/execution cost metric. If byte
  level state growth is later measured, it can be added as a separate column.
- MPT proof generation is currently represented by proof query stages such as
  `dpkiMptProofHttpQuery` and `dpkiOnchainMptProofHttpQuery`, which include
  repository proof construction/retrieval plus local transport. If server-side
  proof construction is instrumented separately later, this table can be
  regenerated with the new stage name included.
