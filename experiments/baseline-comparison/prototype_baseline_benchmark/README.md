# Baseline Comparison Prototype Benchmark

This directory contains the baseline-comparison overhead benchmark. It does not
modify the parameter-sweep or availability plotting scripts.

## Request classes

- `proposed-dpki / management`: CSR generation, X.509 issuance/status update,
  on-chain record, and two assertions for request/response.
- `proposed-dpki / intra-off-chain`: certificate verification, MPT verification,
  one assertion.
- `proposed-dpki / intra-on-chain`: certificate verification, MPT verification,
  on-chain authentication record, on-chain state read, one assertion.
- `proposed-dpki / cross-on-chain`: certificate verification, two MPT
  verifications, on-chain authentication record, on-chain state read, two
  assertions.
- `traditional-pki / management`: CSR generation, X.509 issuance/status update,
  and two assertions for request/response.
- `traditional-pki / intra-auth`: certificate verification, OCSP verification,
  one assertion.
- `traditional-pki / cross-auth`: four PKI authentication hops, i.e.,
  certificate verification, OCSP verification, and assertion repeated four times.
- `threshold-validation-dpki / management`: CSR generation, threshold issuance,
  on-chain evidence, and two assertions for request/response.
- `threshold-validation-dpki / intra-auth`: 4-of-6 parallel validator responses
  and one assertion. The validator response includes certificate/state checking.
- `threshold-validation-dpki / cross-auth`: threshold validation, one extra OCSP
  validation for the peer CA, and two assertions.
- `full-contract-onchain / management`: certificate generation, status
  initialization, and storage by contract, with two assertions for
  request/response.
- `full-contract-onchain / intra-on-chain`: contract-based certificate/status
  checking, authentication-result storage, and one assertion.
- `full-contract-onchain / cross-on-chain`: contract-based certificate/status
  checking, one extra OCSP validation for the peer CA, authentication-result
  storage, and one assertion.

## Timing scope

`totalServiceMs` is the sum of measured service stages. For on-chain stages, the
latency includes local contract execution simulation (`estimateGas`), signing,
and transaction submission. PoW mining and receipt waiting are excluded from the
paper-stage latency because queueing and block-confirmation are modeled
separately. Every transaction is still sent and waited for, and the excluded
confirmation component is preserved separately as `receiptWaitMs` for audit.

The main benchmark runs request classes in a seeded mixed order for each index,
rather than executing one request class as a long batch.

## Outputs

- `request_metrics.csv`: per-request stage measurements.
- `summary_by_request_class.csv`: mean, variance, standard deviation, mean
  absolute deviation, median, p95, min, and max by request class.
- `manifest.json`: run configuration.

## Retained final run

The baseline-comparison folder keeps one retained final overhead run for table regeneration:

- `outputs/actual_overhead_stagebreakdown_receiptgas_onegroup_rich_20260708_3`
