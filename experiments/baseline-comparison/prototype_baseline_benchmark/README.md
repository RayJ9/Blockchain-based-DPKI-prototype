# Baseline Latency Prototype

This directory contains the executable baseline-latency benchmark. It runs the
four authentication platforms against the same OpenSSL services and Omnilink
PoW chain without modifying the parameter-sweep or availability experiments.

## Request classes

- `proposed-dpki / management`: X.509 issuance, on-chain certificate record,
  and request/response assertions.
- `proposed-dpki / intra-off-chain`: certificate verification, complete MPT
  processing, and one assertion.
- `proposed-dpki / intra-on-chain`: the off-chain checks plus authentication
  record commit and state read.
- `proposed-dpki / cross-on-chain`: certificate verification, two MPT proofs,
  authentication record commit, state read, and one end-to-end assertion.
- `traditional-pki`: management, one-hop intra-domain authentication, and a
  four-hop cross-domain process based on certificate and OCSP verification.
- `threshold-validation-dpki`: parallel 4-of-6 CA validation for authentication
  and parallel CA participation during certificate management.
- `full-contract-onchain`: certificate, status, assertion, and result-recording
  operations executed through the full-contract workflow.

## Timing scope

`totalServiceMs` is the sum of measured service stages. Request classes run in
a seeded mixed order rather than in long per-class batches. Every transaction
is sent to the real chain and waited for. Receipt information is retained in
the raw log, while the comparison summary contains latency metrics only.

## Outputs

- `request_metrics.csv`: per-request stage measurements and raw audit fields.
- `summary_by_request_class.csv`: latency mean, variance, standard deviation,
  mean absolute deviation, median, p95, minimum, and maximum.
- `manifest.json`: run configuration and timing scope.
