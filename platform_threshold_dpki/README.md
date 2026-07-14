# Multi-CA threshold DPKI platform

This module implements the 4-of-6 Multi-CA baseline. Management distributes a
certificate request to six CA nodes, aggregates the threshold evidence, and
commits the certificate plus committee signatures. Authentication accepts a
request after four valid CA responses; cross-domain authentication also checks
the counterparty CA status.

`contracts/ThresholdValidationDPKI.sol` exposes the threshold contract path
used by the Fig4 benchmark. The benchmark runner supplies six deterministic
validator accounts and requires four distinct signatures.
