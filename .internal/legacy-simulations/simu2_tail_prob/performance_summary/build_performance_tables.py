from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
SIMU_DIR = SCRIPT_DIR.parent
DEFAULT_OUTPUT = SCRIPT_DIR / "result"


def to_float(value: Any, default: float = math.nan) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def to_int(value: Any, default: int = 0) -> int:
    number = to_float(value, math.nan)
    if math.isnan(number):
        return default
    return int(number)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def percentile(values: list[float], q: float) -> float:
    clean = sorted(v for v in values if not math.isnan(v))
    if not clean:
        return math.nan
    if len(clean) == 1:
        return clean[0]
    pos = (len(clean) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return clean[lo]
    weight = pos - lo
    return clean[lo] * (1.0 - weight) + clean[hi] * weight


def summarize(values: Iterable[float]) -> dict[str, float | int]:
    clean = [float(v) for v in values if not math.isnan(float(v))]
    count = len(clean)
    if count == 0:
        return {
            "count": 0,
            "mean": math.nan,
            "std": math.nan,
            "cv": math.nan,
            "min": math.nan,
            "p50": math.nan,
            "p90": math.nan,
            "p95": math.nan,
            "p99": math.nan,
            "max": math.nan,
        }
    mean = sum(clean) / count
    if count > 1:
        variance = sum((value - mean) ** 2 for value in clean) / (count - 1)
        std = math.sqrt(variance)
    else:
        std = 0.0
    return {
        "count": count,
        "mean": mean,
        "std": std,
        "cv": std / mean if mean else math.nan,
        "min": min(clean),
        "p50": percentile(clean, 0.50),
        "p90": percentile(clean, 0.90),
        "p95": percentile(clean, 0.95),
        "p99": percentile(clean, 0.99),
        "max": max(clean),
    }


def fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(number):
        return ""
    return f"{number:.{digits}f}"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def collect_service_probe(service_probe_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    workflow_samples: list[dict[str, Any]] = []
    stage_samples: list[dict[str, Any]] = []

    for detail_path in sorted(service_probe_dir.glob("*/detailed_requests.csv")):
        probe = detail_path.parent.name
        for row in read_csv(detail_path):
            model = row.get("model", "")
            kind = row.get("kind", "")
            workflow_samples.append(
                {
                    "sourceFile": str(detail_path),
                    "probe": probe,
                    "model": model,
                    "kind": kind,
                    "latencyMs": to_float(row.get("latencyMs")),
                    "queueMs": to_float(row.get("queueMs")),
                    "serviceMs": to_float(row.get("serviceMs")),
                    "chainReads": to_float(row.get("chainReads")),
                    "verifiedCertificateSteps": to_float(row.get("verifiedCertificateSteps")),
                    "proofNodes": to_float(row.get("proofNodes")),
                    "chainTxCount": to_float(row.get("chainTxCount")),
                }
            )
            timings = row.get("stageTimingsJson", "")
            if not timings:
                continue
            try:
                stage_data = json.loads(timings)
            except json.JSONDecodeError:
                continue
            for stage, value in stage_data.items():
                stage_samples.append(
                    {
                        "sourceFile": str(detail_path),
                        "probe": probe,
                        "model": model,
                        "kind": kind,
                        "stage": stage,
                        "latencyMs": to_float(value),
                    }
                )

    return workflow_samples, stage_samples


def workflow_rows_from_samples(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for sample in samples:
        grouped[(sample["model"], sample["kind"])].append(sample)

    rows: list[dict[str, Any]] = []
    for (model, kind), group in sorted(grouped.items()):
        latency = summarize(sample["latencyMs"] for sample in group)
        queue = summarize(sample["queueMs"] for sample in group)
        service = summarize(sample["serviceMs"] for sample in group)
        chain_reads = summarize(sample["chainReads"] for sample in group)
        proof_nodes = summarize(sample["proofNodes"] for sample in group)
        cert_steps = summarize(sample["verifiedCertificateSteps"] for sample in group)
        tx_count = summarize(sample["chainTxCount"] for sample in group)
        rows.append(
            {
                "model": model,
                "kind": kind,
                "count": latency["count"],
                "meanLatencyMs": latency["mean"],
                "medianLatencyMs": latency["p50"],
                "p90LatencyMs": latency["p90"],
                "p95LatencyMs": latency["p95"],
                "p99LatencyMs": latency["p99"],
                "maxLatencyMs": latency["max"],
                "stdLatencyMs": latency["std"],
                "cvLatency": latency["cv"],
                "meanQueueMs": queue["mean"],
                "meanServiceMs": service["mean"],
                "meanChainReads": chain_reads["mean"],
                "meanVerifiedCertificateSteps": cert_steps["mean"],
                "meanProofNodes": proof_nodes["mean"],
                "meanChainTxCount": tx_count["mean"],
                "source": "service_probe detailed_requests",
            }
        )
    return rows


def fallback_workflow_rows(combined_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(combined_path):
        rows.append(
            {
                "model": row.get("model", ""),
                "kind": row.get("kind", ""),
                "count": to_int(row.get("count")),
                "meanLatencyMs": to_float(row.get("meanMs")),
                "medianLatencyMs": to_float(row.get("p50EmpMs")),
                "p90LatencyMs": to_float(row.get("p90EmpMs")),
                "p95LatencyMs": to_float(row.get("p95EmpMs")),
                "p99LatencyMs": to_float(row.get("p99Ms")),
                "maxLatencyMs": to_float(row.get("maxMs")),
                "stdLatencyMs": to_float(row.get("stdMs")),
                "cvLatency": to_float(row.get("cv")),
                "meanQueueMs": math.nan,
                "meanServiceMs": math.nan,
                "meanChainReads": math.nan,
                "meanVerifiedCertificateSteps": math.nan,
                "meanProofNodes": math.nan,
                "meanChainTxCount": math.nan,
                "source": str(combined_path),
            }
        )
    return rows


def stage_rows_from_samples(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    sources: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for sample in samples:
        key = (sample["model"], sample["kind"], sample["stage"])
        grouped[key].append(sample["latencyMs"])
        sources[key].add(sample["sourceFile"])

    rows: list[dict[str, Any]] = []
    for (model, kind, stage), values in sorted(grouped.items()):
        stat = summarize(values)
        rows.append(
            {
                "model": model,
                "kind": kind,
                "stage": stage,
                "count": stat["count"],
                "meanMs": stat["mean"],
                "medianMs": stat["p50"],
                "p90Ms": stat["p90"],
                "p95Ms": stat["p95"],
                "p99Ms": stat["p99"],
                "minMs": stat["min"],
                "maxMs": stat["max"],
                "stdMs": stat["std"],
                "cv": stat["cv"],
                "source": "; ".join(sorted(sources[(model, kind, stage)])),
            }
        )
    return rows


def chain_transaction_rows(tx_path: Path) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(tx_path):
        method = row.get("method", "")
        if method:
            grouped[method].append(row)

    rows: list[dict[str, Any]] = []
    for method, group in sorted(grouped.items()):
        total = summarize(to_float(row.get("totalMs")) for row in group)
        receipt = summarize(to_float(row.get("receiptTotalMs")) for row in group)
        hash_to_receipt = summarize(to_float(row.get("hashToReceiptMs")) for row in group)
        submit = summarize(to_float(row.get("submitToHashMs")) for row in group)
        gas_used = summarize(to_float(row.get("gasUsed")) for row in group)
        gas_limit = summarize(to_float(row.get("gasLimit")) for row in group)
        receipt_polls = summarize(to_float(row.get("receiptPolls")) for row in group)
        success = [
            1.0
            for row in group
            if str(row.get("status", "")).strip().lower() in {"true", "1", "success"}
        ]
        rows.append(
            {
                "method": method,
                "count": total["count"],
                "successRate": len(success) / len(group) if group else math.nan,
                "meanTotalMs": total["mean"],
                "medianTotalMs": total["p50"],
                "p95TotalMs": total["p95"],
                "p99TotalMs": total["p99"],
                "maxTotalMs": total["max"],
                "meanReceiptTotalMs": receipt["mean"],
                "p95ReceiptTotalMs": receipt["p95"],
                "meanHashToReceiptMs": hash_to_receipt["mean"],
                "p95HashToReceiptMs": hash_to_receipt["p95"],
                "meanSubmitToHashMs": submit["mean"],
                "p95SubmitToHashMs": submit["p95"],
                "meanReceiptPolls": receipt_polls["mean"],
                "meanGasUsed": gas_used["mean"],
                "medianGasUsed": gas_used["p50"],
                "p95GasUsed": gas_used["p95"],
                "maxGasUsed": gas_used["max"],
                "meanGasLimit": gas_limit["mean"],
                "source": str(tx_path),
            }
        )
    return rows


def index_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(row.get(key) for key in keys): row for row in rows}


def combine_stage(
    stage_rows: list[dict[str, Any]],
    stage_names: set[str],
    model: str = "DPKI",
) -> dict[str, Any] | None:
    selected = [
        row
        for row in stage_rows
        if row.get("model") == model and str(row.get("stage")) in stage_names
    ]
    if not selected:
        return None
    total_count = sum(to_int(row.get("count")) for row in selected)
    weighted_mean = weighted_value(selected, "meanMs")
    weighted_p95 = weighted_value(selected, "p95Ms")
    weighted_p99 = weighted_value(selected, "p99Ms")
    return {
        "count": total_count,
        "meanLatencyMs": weighted_mean,
        "p95LatencyMs": weighted_p95,
        "p99LatencyMs": weighted_p99,
        "source": "; ".join(sorted({str(row.get("source", "")) for row in selected if row.get("source")})),
    }


def weighted_value(rows: list[dict[str, Any]], field: str) -> float:
    numerator = 0.0
    denominator = 0
    for row in rows:
        count = to_int(row.get("count"))
        value = to_float(row.get(field))
        if count > 0 and not math.isnan(value):
            numerator += count * value
            denominator += count
    return numerator / denominator if denominator else math.nan


def practical_cost_rows(
    workflow_rows: list[dict[str, Any]],
    stage_rows: list[dict[str, Any]],
    tx_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    workflows = index_rows(workflow_rows, ("model", "kind"))
    tx_by_method = index_rows(tx_rows, ("method",))

    def from_workflow(operation: str, kind: str, layer: str, note: str) -> dict[str, Any] | None:
        row = workflows.get(("DPKI", kind))
        if not row:
            return None
        return {
            "operation": operation,
            "layer": layer,
            "meanLatencyMs": row.get("meanLatencyMs"),
            "p95LatencyMs": row.get("p95LatencyMs"),
            "p99LatencyMs": row.get("p99LatencyMs"),
            "sampleCount": row.get("count"),
            "meanGasUsed": math.nan,
            "p95GasUsed": math.nan,
            "storageCostMetric": "",
            "notes": note,
            "source": row.get("source", ""),
        }

    def from_tx(operation: str, method: str, layer: str, note: str) -> dict[str, Any] | None:
        row = tx_by_method.get((method,))
        if not row:
            return None
        return {
            "operation": operation,
            "layer": layer,
            "meanLatencyMs": row.get("meanTotalMs"),
            "p95LatencyMs": row.get("p95TotalMs"),
            "p99LatencyMs": row.get("p99TotalMs"),
            "sampleCount": row.get("count"),
            "meanGasUsed": row.get("meanGasUsed"),
            "p95GasUsed": row.get("p95GasUsed"),
            "storageCostMetric": "gasUsed",
            "notes": note,
            "source": row.get("source", ""),
        }

    def from_stage(operation: str, stages: set[str], layer: str, note: str) -> dict[str, Any] | None:
        row = combine_stage(stage_rows, stages)
        if not row:
            return None
        return {
            "operation": operation,
            "layer": layer,
            "meanLatencyMs": row.get("meanLatencyMs"),
            "p95LatencyMs": row.get("p95LatencyMs"),
            "p99LatencyMs": row.get("p99LatencyMs"),
            "sampleCount": row.get("count"),
            "meanGasUsed": math.nan,
            "p95GasUsed": math.nan,
            "storageCostMetric": "",
            "notes": note,
            "source": row.get("source", ""),
        }

    rows = [
        from_tx("Update domain root", "putDomainRoot", "On-chain contract", "Repository-root write"),
        from_tx("Register certificate", "putCertificate", "On-chain contract", "Certificate-state write"),
        from_tx(
            "Register certificate and root",
            "putCertificateAndDomainRoot",
            "On-chain contract",
            "Certificate write plus repository-root update",
        ),
        from_tx(
            "Submit authentication record",
            "authenticate",
            "On-chain contract",
            "Algorithm 2/3 authentication-record insertion",
        ),
        from_stage(
            "Generate/retrieve MPT proof",
            {"dpkiMptProofHttpQuery", "dpkiOnchainMptProofHttpQuery"},
            "Repository service / gateway",
            "Proof construction/retrieval plus local HTTP transport",
        ),
        from_stage(
            "Verify MPT proof",
            {"dpkiMptVerify", "dpkiOnchainMptVerify"},
            "Client/verifier",
            "Hash-path recomputation against on-chain root",
        ),
        from_stage(
            "Verify certificate signature",
            {"dpkiOpenSslVerifyCert", "dpkiOnchainOpenSslVerifyCert"},
            "Client/verifier",
            "OpenSSL certificate verification",
        ),
        from_stage(
            "Sign authentication assertion",
            {"dpkiOffchainAssertionSign", "dpkiOnchainAssertionSign"},
            "Service CA / verifier",
            "ECDSA assertion generation",
        ),
        from_stage(
            "Verify authentication assertion",
            {"dpkiOffchainAssertionVerify", "dpkiOnchainAssertionVerify"},
            "Client/verifier",
            "ECDSA assertion verification",
        ),
        from_stage(
            "Build/update local MPT",
            {"dpkiManagementBuildMpt"},
            "Certificate repository",
            "Local repository update during certificate management",
        ),
        from_workflow(
            "Algorithm 1 end-to-end",
            "intra-off-chain",
            "DPKI workflow",
            "Intra-domain Merkle-proof authentication",
        ),
        from_workflow(
            "Algorithm 2 end-to-end",
            "intra-on-chain",
            "DPKI workflow",
            "Intra-domain on-chain authentication",
        ),
        from_workflow(
            "Algorithm 3 end-to-end",
            "cross-domain",
            "DPKI workflow",
            "Cross-domain authentication",
        ),
        from_workflow(
            "Certificate management end-to-end",
            "management",
            "DPKI workflow",
            "Certificate issuance/repository update/on-chain confirmation",
        ),
    ]
    return [row for row in rows if row is not None]


def write_markdown_table(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [
        "Operation",
        "Layer",
        "Mean latency (ms)",
        "P95 latency (ms)",
        "Mean gas",
        "Notes",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("operation", "")),
                    str(row.get("layer", "")),
                    fmt(row.get("meanLatencyMs"), 2),
                    fmt(row.get("p95LatencyMs"), 2),
                    fmt(row.get("meanGasUsed"), 0),
                    str(row.get("notes", "")),
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> None:
    simu_dir = Path(args.simu_dir)
    service_probe_dir = Path(args.service_probe_dir) if args.service_probe_dir else simu_dir / "service_probe"
    tx_path = Path(args.tx_breakdown) if args.tx_breakdown else simu_dir / "real_chain_tx_breakdown.csv"
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workflow_samples, stage_samples = collect_service_probe(service_probe_dir)
    workflow_rows = workflow_rows_from_samples(workflow_samples)
    if not workflow_rows:
        workflow_rows = fallback_workflow_rows(service_probe_dir / "combined_distribution_check.csv")
    stage_rows = stage_rows_from_samples(stage_samples)
    tx_rows = chain_transaction_rows(tx_path)
    practical_rows = practical_cost_rows(workflow_rows, stage_rows, tx_rows)

    workflow_fields = [
        "model",
        "kind",
        "count",
        "meanLatencyMs",
        "medianLatencyMs",
        "p90LatencyMs",
        "p95LatencyMs",
        "p99LatencyMs",
        "maxLatencyMs",
        "stdLatencyMs",
        "cvLatency",
        "meanQueueMs",
        "meanServiceMs",
        "meanChainReads",
        "meanVerifiedCertificateSteps",
        "meanProofNodes",
        "meanChainTxCount",
        "source",
    ]
    stage_fields = [
        "model",
        "kind",
        "stage",
        "count",
        "meanMs",
        "medianMs",
        "p90Ms",
        "p95Ms",
        "p99Ms",
        "minMs",
        "maxMs",
        "stdMs",
        "cv",
        "source",
    ]
    tx_fields = [
        "method",
        "count",
        "successRate",
        "meanTotalMs",
        "medianTotalMs",
        "p95TotalMs",
        "p99TotalMs",
        "maxTotalMs",
        "meanReceiptTotalMs",
        "p95ReceiptTotalMs",
        "meanHashToReceiptMs",
        "p95HashToReceiptMs",
        "meanSubmitToHashMs",
        "p95SubmitToHashMs",
        "meanReceiptPolls",
        "meanGasUsed",
        "medianGasUsed",
        "p95GasUsed",
        "maxGasUsed",
        "meanGasLimit",
        "source",
    ]
    practical_fields = [
        "operation",
        "layer",
        "meanLatencyMs",
        "p95LatencyMs",
        "p99LatencyMs",
        "sampleCount",
        "meanGasUsed",
        "p95GasUsed",
        "storageCostMetric",
        "notes",
        "source",
    ]

    write_csv(output_dir / "workflow_latency_table.csv", workflow_rows, workflow_fields)
    write_csv(output_dir / "stage_cost_table.csv", stage_rows, stage_fields)
    write_csv(output_dir / "chain_transaction_cost_table.csv", tx_rows, tx_fields)
    write_csv(output_dir / "practical_costs_table.csv", practical_rows, practical_fields)
    write_markdown_table(output_dir / "practical_costs_table.md", practical_rows)

    summary = {
        "sourceFiles": {
            "serviceProbeDir": str(service_probe_dir),
            "txBreakdown": str(tx_path),
        },
        "outputDir": str(output_dir),
        "workflowRows": len(workflow_rows),
        "stageRows": len(stage_rows),
        "chainTransactionRows": len(tx_rows),
        "practicalCostRows": len(practical_rows),
        "notes": [
            "gasUsed is reported as the on-chain execution/storage cost metric.",
            "MPT proof generation is represented by proof query stages unless a separate server-side proof-construction stage is available.",
        ],
    }
    (output_dir / "metric_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote performance summary tables to {output_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build performance-cost tables from saved DPKI prototype measurements."
    )
    parser.add_argument("--simu-dir", default=str(SIMU_DIR))
    parser.add_argument("--service-probe-dir", default="")
    parser.add_argument("--tx-breakdown", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    return parser


def main() -> None:
    build(build_parser().parse_args())


if __name__ == "__main__":
    main()
