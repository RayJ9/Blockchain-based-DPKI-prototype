from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


FIG_NAME = "fig4"
ROOT = Path(__file__).resolve().parent
SUMMARY_CSV = ROOT / "source_data" / "summary_by_request_class_fig7_aligned.csv"
LOCAL_THRESHOLD_SUMMARY_CSV = ROOT / "source_data" / "threshold_summary_by_request_class.csv"
THRESHOLD_SUMMARY_CSV = ROOT.parent / "Fig3" / "threshold_baseline" / "threshold_summary_by_request_class.csv"
FULL_CONTRACT_SUMMARY_CSV = ROOT / "full_contract_baseline" / "full_contract_summary_by_request_class.csv"
SERVICE_PROBE_ROOT = ROOT.parent / "simu2-8-packaged" / "service_probe"
DATA_FILE = ROOT / f"data_{FIG_NAME}.mat"
LATENCY_STATS_CSV = ROOT / "latency_distribution_summary.csv"

STAGE_COLUMNS = [
    "meanIssueUpdateMs",
    "meanServiceProcessingMs",
    "meanAssertionMs",
    "meanContractExecutionMs",
]

SPLIT_STAGE_MAP = {
    ("proposed-dpki", "intra-off-chain"): {
        "probe": "offchain_intra",
        "model": "DPKI",
        "kind": "intra-off-chain",
        "status": [
            "dpkiChainRootRead",
            "dpkiMptProofHttpQuery",
            "dpkiMptProofResponseVerify",
            "dpkiMptProofSignerCertVerify",
            "dpkiMptVerify",
        ],
        "cert": ["dpkiOpenSslVerifyCert", "dpkiOffchainCertTransferHttp"],
        "assertion": ["dpkiOffchainAssertionSign", "dpkiOffchainAssertionVerify"],
    },
    ("proposed-dpki", "intra-on-chain"): {
        "probe": "onchain_intra",
        "model": "DPKI",
        "kind": "intra-on-chain",
        "status": [
            "dpkiOnchainRootRead",
            "dpkiOnchainMptProofHttpQuery",
            "dpkiOnchainMptProofResponseVerify",
            "dpkiOnchainMptProofSignerCertVerify",
            "dpkiOnchainMptVerify",
        ],
        "cert": ["dpkiOnchainOpenSslVerifyCert", "dpkiOnchainCertTransferHttp"],
        "assertion": ["dpkiOnchainAssertionSign", "dpkiOnchainAssertionVerify"],
    },
    ("proposed-dpki", "cross-on-chain"): {
        "probe": "cross_domain",
        "model": "DPKI",
        "kind": "cross-domain",
        "status": [
            "dpkiOnchainRootRead",
            "dpkiOnchainMptProofHttpQuery",
            "dpkiOnchainMptProofResponseVerify",
            "dpkiOnchainMptProofSignerCertVerify",
            "dpkiOnchainMptVerify",
        ],
        "cert": ["dpkiOnchainOpenSslVerifyCert", "dpkiOnchainCertTransferHttp"],
        "assertion": ["dpkiOnchainAssertionSign", "dpkiOnchainAssertionVerify"],
    },
    ("proposed-dpki", "management"): {
        "probe": "management",
        "model": "DPKI",
        "kind": "management",
        "cert": [
            "dpkiManagementOpenSslVerifyIssuerCA",
            "dpkiManagementOpenSslVerifyLeaf",
            "dpkiManagementRepositoryHttpVerify",
        ],
        "assertion": [
            "dpkiManagementIssuerAssertionSign",
            "dpkiManagementIssuerAssertionVerify",
            "dpkiManagementLeafAssertionSign",
            "dpkiManagementLeafAssertionVerify",
        ],
    },
    ("traditional-pki", "intra-auth"): {
        "probe": "offchain_intra",
        "model": "PKI",
        "kind": "intra-pki",
        "status": ["pkiLeafOcspHttpQuery"],
        "cert": ["pkiOpenSslVerifyLeaf", "pkiCertTransferHttp"],
        "assertion": ["pkiOpenSslAssertionSign", "pkiOpenSslAssertionVerify"],
    },
    ("traditional-pki", "cross-auth"): {
        "probe": "cross_domain",
        "model": "PKI",
        "kind": "cross-domain",
        "status": [
            "pkiLeafOcspHttpQuery",
            "pkiRootCAOcspHttpQuery",
            "pkiSourceCAOcspHttpQuery",
            "pkiTargetCAOcspHttpQuery",
        ],
        "cert": [
            "pkiCertTransferHttp",
            "pkiOpenSslVerifyLeaf",
            "pkiOpenSslVerifyRootCA",
            "pkiOpenSslVerifySourceCA",
            "pkiOpenSslVerifyTargetCA",
        ],
        "assertion": [
            "pkiLeafAssertionSign",
            "pkiLeafAssertionVerify",
            "pkiRootCAAssertionSign",
            "pkiRootCAAssertionVerify",
            "pkiSourceCAAssertionSign",
            "pkiSourceCAAssertionVerify",
            "pkiTargetCAAssertionSign",
            "pkiTargetCAAssertionVerify",
        ],
    },
    ("traditional-pki", "management"): {
        "probe": "management",
        "model": "PKI",
        "kind": "management",
        "cert": [
            "pkiManagementOpenSslVerifyIssuerCA",
            "pkiManagementOpenSslVerifyLeaf",
            "pkiManagementRepositoryHttpVerify",
        ],
        "assertion": [
            "pkiManagementIssuerAssertionSign",
            "pkiManagementIssuerAssertionVerify",
            "pkiManagementLeafAssertionSign",
            "pkiManagementLeafAssertionVerify",
        ],
    },
}

THRESHOLD_RATIO_SOURCE = {
    "management": ("proposed-dpki", "management"),
    "intra-off-chain": ("proposed-dpki", "intra-off-chain"),
    "intra-on-chain": ("proposed-dpki", "intra-on-chain"),
    "cross-on-chain": ("proposed-dpki", "cross-on-chain"),
}

ASSERTION_STAGE_PAIRS = [
    ("offchain_intra", "DPKI", "intra-off-chain", ["dpkiOffchainAssertionSign", "dpkiOffchainAssertionVerify"]),
    ("offchain_intra", "PKI", "intra-pki", ["pkiOpenSslAssertionSign", "pkiOpenSslAssertionVerify"]),
    ("onchain_intra", "DPKI", "intra-on-chain", ["dpkiOnchainAssertionSign", "dpkiOnchainAssertionVerify"]),
    ("onchain_intra", "PKI", "intra-pki", ["pkiOpenSslAssertionSign", "pkiOpenSslAssertionVerify"]),
    ("cross_domain", "DPKI", "cross-domain", ["dpkiOnchainAssertionSign", "dpkiOnchainAssertionVerify"]),
    ("cross_domain", "PKI", "cross-domain", ["pkiLeafAssertionSign", "pkiLeafAssertionVerify"]),
    ("management", "DPKI", "management", ["dpkiManagementLeafAssertionSign", "dpkiManagementLeafAssertionVerify"]),
    ("management", "PKI", "management", ["pkiManagementLeafAssertionSign", "pkiManagementLeafAssertionVerify"]),
]


def get_row(df: pd.DataFrame, mechanism: str, request_class: str) -> pd.Series:
    rows = df[(df["mechanism"] == mechanism) & (df["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def load_summary() -> pd.DataFrame:
    df = pd.read_csv(SUMMARY_CSV)
    threshold_source = LOCAL_THRESHOLD_SUMMARY_CSV if LOCAL_THRESHOLD_SUMMARY_CSV.exists() else THRESHOLD_SUMMARY_CSV
    if threshold_source.exists():
        threshold = pd.read_csv(threshold_source)
        df = pd.concat([df[df["mechanism"] != "threshold-validation-dpki"], threshold], ignore_index=True)
    if FULL_CONTRACT_SUMMARY_CSV.exists():
        full_contract = pd.read_csv(FULL_CONTRACT_SUMMARY_CSV)
        cost_columns = [
            "meanGasUsed",
            "meanTxInputBytes",
            "meanRawTxBytes",
            "meanReceiptLogBytes",
            "meanStateWriteBytesEstimated",
            "meanCertChecks",
        ]
        for _, row in full_contract.iterrows():
            mask = (df["mechanism"] == "full-contract-onchain") & (df["requestClass"] == row["requestClass"])
            if not mask.any():
                continue
            for column in cost_columns:
                if column in df.columns and column in full_contract.columns:
                    df.loc[mask, column] = row[column]
    return df


def load_stage_stats() -> dict[str, pd.DataFrame]:
    stats = {}
    for probe_dir in ["offchain_intra", "onchain_intra", "cross_domain", "management"]:
        path = SERVICE_PROBE_ROOT / probe_dir / "stage_statistics.csv"
        if path.exists():
            stats[probe_dir] = pd.read_csv(path)
    return stats


def mean_common_assertion_ms(stats: dict[str, pd.DataFrame]) -> float:
    values = []
    for probe, model, kind, stages in ASSERTION_STAGE_PAIRS:
        if probe not in stats:
            continue
        df = stats[probe]
        rows = df[
            (df["model"] == model)
            & (df["kind"] == kind)
            & (df["stage"].isin(stages))
        ]
        if len(rows) == len(stages):
            values.append(float(rows["meanMs"].sum()))
    if not values:
        return 21.8
    return float(np.mean(values))


def assertion_stage_reference(row: pd.Series) -> tuple[str, str, str, list[str]] | None:
    mechanism = str(row["mechanism"])
    request_class = str(row["requestClass"])
    if mechanism == "full-contract-onchain":
        if request_class == "management":
            return (
                "management",
                "DPKI",
                "management",
                ["dpkiManagementLeafAssertionSign", "dpkiManagementLeafAssertionVerify"],
            )
        if request_class == "cross-on-chain":
            return (
                "cross_domain",
                "DPKI",
                "cross-domain",
                ["dpkiOnchainAssertionSign", "dpkiOnchainAssertionVerify"],
            )
        return (
            "onchain_intra",
            "DPKI",
            "intra-on-chain",
            ["dpkiOnchainAssertionSign", "dpkiOnchainAssertionVerify"],
        )
    if mechanism == "threshold-validation-dpki":
        ref_mechanism, ref_class = THRESHOLD_RATIO_SOURCE.get(request_class, ("proposed-dpki", "intra-off-chain"))
        ref_row = pd.Series({"mechanism": ref_mechanism, "requestClass": ref_class})
        return assertion_stage_reference(ref_row)
    if mechanism == "traditional-pki" and request_class == "cross-auth":
        return (
            "cross_domain",
            "PKI",
            "cross-domain",
            ["pkiLeafAssertionSign", "pkiLeafAssertionVerify"],
        )
    if mechanism == "traditional-pki" and request_class == "management":
        return (
            "management",
            "PKI",
            "management",
            ["pkiManagementLeafAssertionSign", "pkiManagementLeafAssertionVerify"],
        )
    if mechanism == "proposed-dpki" and request_class == "management":
        return (
            "management",
            "DPKI",
            "management",
            ["dpkiManagementLeafAssertionSign", "dpkiManagementLeafAssertionVerify"],
        )
    spec = SPLIT_STAGE_MAP.get((mechanism, request_class))
    if spec is None:
        return None
    return (
        str(spec["probe"]),
        str(spec["model"]),
        str(spec["kind"]),
        list(spec.get("assertion", [])),
    )


def measured_assertion_ms(row: pd.Series, stats: dict[str, pd.DataFrame], fallback_ms: float) -> float:
    ref = assertion_stage_reference(row)
    if ref is None:
        return fallback_ms
    probe, model, kind, stage_names = ref
    if not stage_names or probe not in stats:
        return fallback_ms
    df = stats[probe]
    rows = df[
        (df["model"] == model)
        & (df["kind"] == kind)
        & (df["stage"].isin(stage_names))
    ]
    found = set(rows["stage"].tolist())
    if any(name not in found for name in stage_names):
        return fallback_ms
    return float(rows["meanMs"].sum())


def sum_probe_stages(stats: dict[str, pd.DataFrame], spec: dict[str, object], names: list[str]) -> float:
    if not names:
        return 0.0
    probe = str(spec["probe"])
    if probe not in stats:
        return 0.0
    df = stats[probe]
    rows = df[
        (df["model"] == str(spec["model"]))
        & (df["kind"] == str(spec["kind"]))
        & (df["stage"].isin(names))
    ]
    found = set(rows["stage"].tolist())
    missing = [name for name in names if name not in found]
    if missing:
        raise ValueError(f"Missing service-probe stages for {spec['model']}/{spec['kind']}: {missing}")
    return float(rows["meanMs"].sum())


def real_management_issue_ms(mechanism: str, stats: dict[str, pd.DataFrame]) -> float | None:
    if "management" not in stats:
        return None
    df = stats["management"]
    if mechanism in {"proposed-dpki", "threshold-validation-dpki"}:
        rows = df[
            (df["model"] == "DPKI")
            & (df["kind"] == "management")
            & (df["stage"] == "dpkiManagementIssueCertificate")
        ]
        if len(rows) == 1:
            return float(rows.iloc[0]["meanMs"])
    if mechanism == "traditional-pki":
        stages = [
            "pkiOpenSslIssueCsr",
            "pkiOpenSslIssueExtractPubkey",
            "pkiOpenSslIssueKeygen",
            "pkiOpenSslIssueSignCert",
        ]
        rows = df[
            (df["model"] == "PKI")
            & (df["kind"] == "management")
            & (df["stage"].isin(stages))
        ]
        if len(rows) == len(stages):
            return float(rows["meanMs"].sum())
    return None


def split_cert_and_assertion(
    row: pd.Series,
    stats: dict[str, pd.DataFrame],
) -> tuple[float, float]:
    key = (str(row["mechanism"]), str(row["requestClass"]))
    if key[0] == "threshold-validation-dpki":
        return float(row["meanCertVerificationMs"]), 0.0
    spec = SPLIT_STAGE_MAP.get(key)

    cert_bucket = float(row["meanCertVerificationMs"])
    if spec is None or cert_bucket <= 0:
        return cert_bucket, 0.0

    cert_raw = sum_probe_stages(stats, spec, list(spec.get("cert", [])))
    assertion_raw = sum_probe_stages(stats, spec, list(spec.get("assertion", [])))
    raw_total = cert_raw + assertion_raw
    if raw_total <= 0:
        return cert_bucket, 0.0
    cert_ms = cert_bucket * cert_raw / raw_total
    assertion_ms = cert_bucket - cert_ms
    return cert_ms, assertion_ms


def measured_service_processing_ms(row: pd.Series, stats: dict[str, pd.DataFrame]) -> float | None:
    spec = SPLIT_STAGE_MAP.get((str(row["mechanism"]), str(row["requestClass"])))
    if spec is None:
        return None
    status_ms = sum_probe_stages(stats, spec, list(spec.get("status", [])))
    cert_ms = sum_probe_stages(stats, spec, list(spec.get("cert", [])))
    measured = status_ms + cert_ms
    return measured if measured > 0 else None


def scaled_distribution_totals(row: pd.Series, mean_total: float) -> tuple[float, float, float]:
    source_mean = float(row["meanNormalizedLatencyMs"])
    if source_mean <= 0:
        return mean_total, mean_total, 0.0
    median_total = mean_total * float(row["medianNormalizedLatencyMs"]) / source_mean
    p95_total = mean_total * float(row["p95NormalizedLatencyMs"]) / source_mean
    if "stdNormalizedLatencyMs" in row.index and not pd.isna(row["stdNormalizedLatencyMs"]):
        std_total = mean_total * float(row["stdNormalizedLatencyMs"]) / source_mean
    else:
        std_total = max(0.0, p95_total - mean_total) / 1.645
    return max(0.0, median_total), max(median_total, p95_total), max(0.0, std_total)


def row_stages(row: pd.Series, stats: dict[str, pd.DataFrame], common_assertion_ms: float) -> list[float]:
    assertion_ms = measured_assertion_ms(row, stats, common_assertion_ms)
    if str(row["mechanism"]) == "full-contract-onchain":
        issue_ms = float(row["meanIssueUpdateMs"]) if str(row["requestClass"]) == "management" else 0.0
        contract_ms = float(row["meanContractExecutionMs"])
        if contract_ms <= 0:
            contract_ms = float(row["meanNormalizedLatencyMs"]) - issue_ms
        return [
            issue_ms,
            0.0,
            assertion_ms,
            contract_ms,
        ]
    cert_ms, _discarded_old_assertion_ms = split_cert_and_assertion(row, stats)
    issue_ms = float(row["meanIssueUpdateMs"])
    if str(row["requestClass"]) == "management":
        measured_issue_ms = real_management_issue_ms(str(row["mechanism"]), stats)
        if measured_issue_ms is not None:
            issue_ms = measured_issue_ms
        service_processing_ms = 0.0
    else:
        service_processing_ms = measured_service_processing_ms(row, stats)
        if service_processing_ms is None:
            service_processing_ms = float(row["meanStatusValidationMs"]) + cert_ms
    return [
        issue_ms,
        service_processing_ms,
        assertion_ms,
        float(row["meanContractExecutionMs"]),
    ]


def panel(
    df: pd.DataFrame,
    stats: dict[str, pd.DataFrame],
    panel_name: str,
    specs: list[tuple[str, str, str]],
    assertion_ms: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict[str, object]]]:
    labels = []
    stages = []
    totals = []
    medians = []
    p95s = []
    stds = []
    stats_rows = []
    for label, mechanism, request_class in specs:
        row = get_row(df, mechanism, request_class)
        labels.append(label)
        stage_values = row_stages(row, stats, assertion_ms)
        mean_total = float(sum(stage_values))
        median_total, p95_total, std_total = scaled_distribution_totals(row, mean_total)
        stages.append(stage_values)
        totals.append(mean_total)
        medians.append(median_total)
        p95s.append(p95_total)
        stds.append(std_total)
        stats_rows.append(
            {
                "panel": panel_name,
                "label": label,
                "mechanism": mechanism,
                "requestClass": request_class,
                "meanMs": mean_total,
                "medianMs": median_total,
                "p95Ms": p95_total,
                "stdMs": std_total,
                "varianceMs2": std_total * std_total,
                "issueUpdateMs": stage_values[0],
                "serviceProcessingMs": stage_values[1],
                "assertionMs": stage_values[2],
                "contractExecutionMs": stage_values[3],
            }
        )
    return (
        np.array(labels, dtype=object).reshape(-1, 1),
        np.array(stages, dtype=float),
        np.array(totals, dtype=float).reshape(-1, 1),
        np.array(medians, dtype=float).reshape(-1, 1),
        np.array(p95s, dtype=float).reshape(-1, 1),
        np.array(stds, dtype=float).reshape(-1, 1),
        stats_rows,
    )


def cost_panel(df: pd.DataFrame, column: str) -> np.ndarray:
    specs = [
        ("intra-on-chain", "intra-on-chain", "intra-on-chain"),
        ("cross-on-chain", "cross-on-chain", "cross-on-chain"),
    ]
    mechanisms = ["proposed-dpki", "threshold-validation-dpki", "full-contract-onchain"]
    values = np.zeros((len(specs), len(mechanisms)), dtype=float)
    for r, (_, dpki_class, other_class) in enumerate(specs):
        for c, mechanism in enumerate(mechanisms):
            request_class = dpki_class if mechanism in {"proposed-dpki", "threshold-validation-dpki"} else other_class
            values[r, c] = float(get_row(df, mechanism, request_class)[column])
    return values


def onchain_record_panel(df: pd.DataFrame) -> np.ndarray:
    specs = [
        ("intra-on-chain", "intra-on-chain", "intra-on-chain"),
        ("cross-on-chain", "cross-on-chain", "cross-on-chain"),
    ]
    mechanisms = ["proposed-dpki", "threshold-validation-dpki", "full-contract-onchain"]
    values = np.zeros((len(specs), len(mechanisms)), dtype=float)
    for r, (_, dpki_class, other_class) in enumerate(specs):
        for c, mechanism in enumerate(mechanisms):
            request_class = dpki_class if mechanism in {"proposed-dpki", "threshold-validation-dpki"} else other_class
            row = get_row(df, mechanism, request_class)
            tx_bytes = max(float(row["meanRawTxBytes"]), float(row["meanTxInputBytes"]))
            values[r, c] = (
                tx_bytes
                + float(row["meanReceiptLogBytes"])
                + float(row["meanStateWriteBytesEstimated"])
            )
    return values


def main() -> None:
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Missing source CSV: {SUMMARY_CSV}")
    df = load_summary()
    stats = load_stage_stats()
    assertion_ms = mean_common_assertion_ms(stats)

    mgmt_labels, mgmt_stages, mgmt_totals, mgmt_medians, mgmt_p95s, mgmt_stds, mgmt_stats = panel(
        df,
        stats,
        "Management",
        [
            ("Threshold-validation DPKI", "threshold-validation-dpki", "management"),
            ("Traditional PKI", "traditional-pki", "management"),
            ("Full-contract on-chain DPKI", "full-contract-onchain", "management"),
            ("Our-proposed DPKI", "proposed-dpki", "management"),
        ],
        assertion_ms,
    )
    intra_labels, intra_stages, intra_totals, intra_medians, intra_p95s, intra_stds, intra_stats = panel(
        df,
        stats,
        "Intra-domain authentication",
        [
            ("Threshold-validation DPKI (off-chain)", "threshold-validation-dpki", "intra-off-chain"),
            ("Traditional PKI", "traditional-pki", "intra-auth"),
            ("Threshold-validation DPKI (on-chain)", "threshold-validation-dpki", "intra-on-chain"),
            ("Full-contract on-chain DPKI", "full-contract-onchain", "intra-on-chain"),
            ("Our-proposed DPKI (Alg. 1)", "proposed-dpki", "intra-off-chain"),
            ("Our-proposed DPKI (Alg. 2)", "proposed-dpki", "intra-on-chain"),
        ],
        assertion_ms,
    )
    cross_labels, cross_stages, cross_totals, cross_medians, cross_p95s, cross_stds, cross_stats = panel(
        df,
        stats,
        "Cross-domain authentication",
        [
            ("Traditional PKI", "traditional-pki", "cross-auth"),
            ("Threshold-validation DPKI", "threshold-validation-dpki", "cross-on-chain"),
            ("Full-contract on-chain DPKI", "full-contract-onchain", "cross-on-chain"),
            ("Our-proposed DPKI (Alg. 3)", "proposed-dpki", "cross-on-chain"),
        ],
        assertion_ms,
    )

    gas_values = cost_panel(df, "meanGasUsed") / 1000.0
    record_values = onchain_record_panel(df)
    pd.DataFrame(intra_stats + cross_stats + mgmt_stats).to_csv(LATENCY_STATS_CSV, index=False)

    savemat(
        DATA_FILE,
        {
            "stageNames": np.array(["Issue/update", "Service processing", "Assertion", "Contract"], dtype=object).reshape(-1, 1),
            "commonAssertionMs": np.array([[assertion_ms]], dtype=float),
            "stageColors": np.array(
                [
                    [245, 219, 182],
                    [200, 212, 233],
                    [216, 226, 184],
                    [245, 151, 144],
                ],
                dtype=float,
            )
            / 255.0,
            "mechanismColors": np.array(
                [
                    [154, 129, 186],
                    [229, 190, 105],
                    [132, 168, 160],
                ],
                dtype=float,
            )
            / 255.0,
            "statusColors": np.array(
                [
                    [158, 170, 209],
                    [245, 151, 144],
                    [167, 204, 159],
                    [245, 219, 182],
                ],
                dtype=float,
            )
            / 255.0,
            "mgmtLabels": mgmt_labels,
            "mgmtStages": mgmt_stages,
            "mgmtTotals": mgmt_totals,
            "mgmtMedianTotals": mgmt_medians,
            "mgmtP95Totals": mgmt_p95s,
            "mgmtStdTotals": mgmt_stds,
            "intraLabels": intra_labels,
            "intraStages": intra_stages,
            "intraTotals": intra_totals,
            "intraMedianTotals": intra_medians,
            "intraP95Totals": intra_p95s,
            "intraStdTotals": intra_stds,
            "crossLabels": cross_labels,
            "crossStages": cross_stages,
            "crossTotals": cross_totals,
            "crossMedianTotals": cross_medians,
            "crossP95Totals": cross_p95s,
            "crossStdTotals": cross_stds,
            "costRequestLabels": np.array(["Intra-domain auth.", "Cross-domain auth."], dtype=object).reshape(-1, 1),
            "costMechanismLabels": np.array(
                ["Our-proposed DPKI", "Threshold-validation DPKI", "Full-contract on-chain DPKI"],
                dtype=object,
            ).reshape(-1, 1),
            "gasValues": gas_values,
            "recordValues": record_values,
        },
    )
    print(f"Saved {DATA_FILE}")


if __name__ == "__main__":
    main()
