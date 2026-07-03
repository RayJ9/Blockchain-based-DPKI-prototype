from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


FIG_NAME = "fig4"
ROOT = Path(__file__).resolve().parent
SUMMARY_CSV = ROOT / "source_data" / "summary_by_request_class_fig7_aligned.csv"
if not SUMMARY_CSV.exists():
    SUMMARY_CSV = ROOT / "source_data" / "summary_by_request_class_no_authsig.csv"
THRESHOLD_SUMMARY_CSV = ROOT.parent / "Fig3" / "threshold_baseline" / "threshold_summary_by_request_class.csv"
SERVICE_PROBE_ROOT = ROOT.parent / "simu2-8-packaged" / "service_probe"
DATA_FILE = ROOT / f"data_{FIG_NAME}.mat"

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
        "cert": ["dpkiOpenSslVerifyCert", "dpkiOffchainCertTransferHttp"],
        "assertion": ["dpkiOffchainAssertionSign", "dpkiOffchainAssertionVerify"],
    },
    ("proposed-dpki", "intra-on-chain"): {
        "probe": "onchain_intra",
        "model": "DPKI",
        "kind": "intra-on-chain",
        "cert": ["dpkiOnchainOpenSslVerifyCert", "dpkiOnchainCertTransferHttp"],
        "assertion": ["dpkiOnchainAssertionSign", "dpkiOnchainAssertionVerify"],
    },
    ("proposed-dpki", "cross-on-chain"): {
        "probe": "cross_domain",
        "model": "DPKI",
        "kind": "cross-domain",
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
        "cert": ["pkiOpenSslVerifyLeaf", "pkiCertTransferHttp"],
        "assertion": ["pkiOpenSslAssertionSign", "pkiOpenSslAssertionVerify"],
    },
    ("traditional-pki", "cross-auth"): {
        "probe": "cross_domain",
        "model": "PKI",
        "kind": "cross-domain",
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


def get_row(df: pd.DataFrame, mechanism: str, request_class: str) -> pd.Series:
    rows = df[(df["mechanism"] == mechanism) & (df["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def load_summary() -> pd.DataFrame:
    df = pd.read_csv(SUMMARY_CSV)
    if THRESHOLD_SUMMARY_CSV.exists():
        threshold = pd.read_csv(THRESHOLD_SUMMARY_CSV)
        df = pd.concat([df[df["mechanism"] != "threshold-validation-dpki"], threshold], ignore_index=True)
    return df


def load_stage_stats() -> dict[str, pd.DataFrame]:
    stats = {}
    for probe_dir in ["offchain_intra", "onchain_intra", "cross_domain", "management"]:
        path = SERVICE_PROBE_ROOT / probe_dir / "stage_statistics.csv"
        if path.exists():
            stats[probe_dir] = pd.read_csv(path)
    return stats


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
        source_key = THRESHOLD_RATIO_SOURCE.get(key[1])
        spec = SPLIT_STAGE_MAP.get(source_key) if source_key is not None else None
    else:
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


def row_stages(row: pd.Series, stats: dict[str, pd.DataFrame]) -> list[float]:
    if str(row["mechanism"]) == "full-contract-onchain":
        return [
            0.0,
            0.0,
            0.0,
            float(row["meanNormalizedLatencyMs"]),
        ]
    cert_ms, assertion_ms = split_cert_and_assertion(row, stats)
    issue_ms = float(row["meanIssueUpdateMs"])
    if str(row["requestClass"]) == "management":
        measured_issue_ms = real_management_issue_ms(str(row["mechanism"]), stats)
        if measured_issue_ms is not None:
            issue_ms = measured_issue_ms
        service_processing_ms = 0.0
    else:
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
    specs: list[tuple[str, str, str]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    labels = []
    stages = []
    totals = []
    for label, mechanism, request_class in specs:
        row = get_row(df, mechanism, request_class)
        labels.append(label)
        stage_values = row_stages(row, stats)
        stages.append(stage_values)
        totals.append(float(sum(stage_values)))
    return np.array(labels, dtype=object).reshape(-1, 1), np.array(stages, dtype=float), np.array(totals, dtype=float).reshape(-1, 1)


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

    mgmt_labels, mgmt_stages, mgmt_totals = panel(
        df,
        stats,
        [
            ("Threshold-validation DPKI", "threshold-validation-dpki", "management"),
            ("Traditional PKI", "traditional-pki", "management"),
            ("Full-contract on-chain DPKI", "full-contract-onchain", "management"),
            ("Our-proposed DPKI", "proposed-dpki", "management"),
        ],
    )
    intra_labels, intra_stages, intra_totals = panel(
        df,
        stats,
        [
            ("Threshold-validation DPKI (off-chain)", "threshold-validation-dpki", "intra-off-chain"),
            ("Traditional PKI", "traditional-pki", "intra-auth"),
            ("Threshold-validation DPKI (on-chain)", "threshold-validation-dpki", "intra-on-chain"),
            ("Full-contract on-chain DPKI", "full-contract-onchain", "intra-on-chain"),
            ("Our-proposed DPKI (Alg. 1)", "proposed-dpki", "intra-off-chain"),
            ("Our-proposed DPKI (Alg. 2)", "proposed-dpki", "intra-on-chain"),
        ],
    )
    cross_labels, cross_stages, cross_totals = panel(
        df,
        stats,
        [
            ("Traditional PKI", "traditional-pki", "cross-auth"),
            ("Threshold-validation DPKI", "threshold-validation-dpki", "cross-on-chain"),
            ("Full-contract on-chain DPKI", "full-contract-onchain", "cross-on-chain"),
            ("Our-proposed DPKI (Alg. 3)", "proposed-dpki", "cross-on-chain"),
        ],
    )

    gas_values = cost_panel(df, "meanGasUsed") / 1000.0
    record_values = onchain_record_panel(df)

    savemat(
        DATA_FILE,
        {
            "stageNames": np.array(["Issue/update", "Service processing", "Assertion", "Contract"], dtype=object).reshape(-1, 1),
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
            "intraLabels": intra_labels,
            "intraStages": intra_stages,
            "intraTotals": intra_totals,
            "crossLabels": cross_labels,
            "crossStages": cross_stages,
            "crossTotals": cross_totals,
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
