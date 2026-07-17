# Multi-CA threshold DPKI platform

This module implements the 4-of-6 Multi-CA baseline. Management distributes a
certificate request to six CA nodes, aggregates the threshold evidence, and
commits the certificate plus committee signatures. Authentication accepts a
request after four valid CA responses. The six requests are issued
concurrently, so latency ends at the fourth valid response rather than the sum
of six sequential executions. Each responding CA performs certificate and
status validation. Cross-domain authentication also checks the counterparty CA
status.

`contracts/ThresholdValidationDPKI.sol` exposes the threshold contract path
used by the `baseline-comparison` experiment. The benchmark runner supplies six deterministic
validator accounts and requires four distinct signatures.
