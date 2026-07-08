from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "prototype_baseline_benchmark" / "outputs"
pow_adjusted_runs = sorted(RUN_ROOT.glob("full_2000_pow_adjusted_*"))
if pow_adjusted_runs:
    RUN_DIR = pow_adjusted_runs[-1]
else:
    service_runs = sorted(path for path in RUN_ROOT.glob("full_2000_*") if "receipt" not in path.name)
    RUN_DIR = service_runs[-1]
SUMMARY_CSV = RUN_DIR / "summary_by_request_class.csv"
DATA_FILE = ROOT / "data_fig4_prototype.mat"
LATENCY_CSV = ROOT / "latency_distribution_summary_prototype.csv"

STAGE_NAMES = [
    "Issue/Update",
    "Cert. verification",
    "Status/proof validation",
    "On-chain record",
    "Contract execution",
    "State read",
    "Assertion",
]

STAGE_COLS = [
    "issueUpdateMs_mean",
    "certificateVerificationMs_mean",
    None,
    "chainRecordMs_mean",
    "contractExecutionMs_mean",
    "chainStateReadMs_mean",
    "assertionMs_mean",
]

STATUS_PARTS = [
    "statusValidationMs_mean",
    "mptValidationMs_mean",
    "thresholdValidationMs_mean",
    "thresholdIssueMs_mean",
]

STAGE_COLORS = np.array([
    [0.36, 0.57, 0.76],
    [0.46, 0.65, 0.42],
    [0.86, 0.55, 0.27],
    [0.58, 0.50, 0.70],
    [0.74, 0.32, 0.30],
    [0.55, 0.55, 0.55],
    [0.72, 0.72, 0.72],
])

MECHANISM_COLORS = np.array([
    [0.44, 0.56, 0.74],
    [0.64, 0.53, 0.73],
    [0.76, 0.43, 0.39],
    [0.43, 0.64, 0.49],
])


def get_row(df: pd.DataFrame, mechanism: str, request_class: str) -> pd.Series:
    rows = df[(df["mechanism"] == mechanism) & (df["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def stage_vector(row: pd.Series) -> list[float]:
    values = []
    for col in STAGE_COLS:
        if col is None:
            values.append(float(sum(row.get(part, 0.0) for part in STATUS_PARTS)))
        else:
            values.append(float(row.get(col, 0.0)))
    return values


def table_for(df: pd.DataFrame, specs: list[tuple[str, str, str]]):
    labels = []
    stages = []
    totals = []
    stds = []
    for label, mechanism, request_class in specs:
        row = get_row(df, mechanism, request_class)
        labels.append(label)
        stages.append(stage_vector(row))
        totals.append(float(row["totalServiceMs_mean"]))
        ci95 = 1.96 * float(row["totalServiceMs_std"]) / np.sqrt(float(row["count"]))
        stds.append(ci95)
    return labels, np.array(stages, dtype=float), np.array(totals, dtype=float), np.array(stds, dtype=float)


def mean_value(df: pd.DataFrame, mechanism: str, request_class: str, column: str) -> float:
    return float(get_row(df, mechanism, request_class).get(column, 0.0))


def main():
    df = pd.read_csv(SUMMARY_CSV)

    intra_specs = [
        ("Traditional PKI", "traditional-pki", "intra-auth"),
        ("Threshold DPKI", "threshold-validation-dpki", "intra-auth"),
        ("Full-contract DPKI", "full-contract-onchain", "intra-on-chain"),
        ("Our-proposed DPKI (off-chain)", "proposed-dpki", "intra-off-chain"),
        ("Our-proposed DPKI (on-chain)", "proposed-dpki", "intra-on-chain"),
    ]
    cross_specs = [
        ("Traditional PKI", "traditional-pki", "cross-auth"),
        ("Threshold DPKI", "threshold-validation-dpki", "cross-auth"),
        ("Full-contract DPKI", "full-contract-onchain", "cross-on-chain"),
        ("Our-proposed DPKI", "proposed-dpki", "cross-on-chain"),
    ]
    mgmt_specs = [
        ("Traditional PKI", "traditional-pki", "management"),
        ("Threshold DPKI", "threshold-validation-dpki", "management"),
        ("Full-contract DPKI", "full-contract-onchain", "management"),
        ("Our-proposed DPKI", "proposed-dpki", "management"),
    ]

    intra_labels, intra_stages, intra_totals, intra_stds = table_for(df, intra_specs)
    cross_labels, cross_stages, cross_totals, cross_stds = table_for(df, cross_specs)
    mgmt_labels, mgmt_stages, mgmt_totals, mgmt_stds = table_for(df, mgmt_specs)

    cost_request_labels = ["Management", "Intra-domain", "Cross-domain"]
    cost_mechanism_labels = [
        "Traditional PKI",
        "Threshold DPKI",
        "Full-contract DPKI",
        "Our-proposed DPKI",
    ]
    cost_specs = {
        "Traditional PKI": [
            ("traditional-pki", "management"),
            ("traditional-pki", "intra-auth"),
            ("traditional-pki", "cross-auth"),
        ],
        "Threshold DPKI": [
            ("threshold-validation-dpki", "management"),
            ("threshold-validation-dpki", "intra-auth"),
            ("threshold-validation-dpki", "cross-auth"),
        ],
        "Full-contract DPKI": [
            ("full-contract-onchain", "management"),
            ("full-contract-onchain", "intra-on-chain"),
            ("full-contract-onchain", "cross-on-chain"),
        ],
        "Our-proposed DPKI": [
            ("proposed-dpki", "management"),
            ("proposed-dpki", "intra-on-chain"),
            ("proposed-dpki", "cross-on-chain"),
        ],
    }
    gas_values = np.zeros((3, 4), dtype=float)
    record_values = np.zeros((3, 4), dtype=float)
    for c, label in enumerate(cost_mechanism_labels):
        for r, (mechanism, request_class) in enumerate(cost_specs[label]):
            gas_values[r, c] = mean_value(df, mechanism, request_class, "gasUsed_mean") / 1000.0
            record_values[r, c] = (
                mean_value(df, mechanism, request_class, "rawTxBytes_mean")
                + mean_value(df, mechanism, request_class, "receiptLogBytes_mean")
            )

    savemat(
        DATA_FILE,
        {
            "stageNames": np.array(STAGE_NAMES, dtype=object),
            "stageColors": STAGE_COLORS,
            "mechanismColors": MECHANISM_COLORS,
            "intraLabels": np.array(intra_labels, dtype=object),
            "intraStages": intra_stages,
            "intraTotals": intra_totals,
            "intraStdTotals": intra_stds,
            "crossLabels": np.array(cross_labels, dtype=object),
            "crossStages": cross_stages,
            "crossTotals": cross_totals,
            "crossStdTotals": cross_stds,
            "mgmtLabels": np.array(mgmt_labels, dtype=object),
            "mgmtStages": mgmt_stages,
            "mgmtTotals": mgmt_totals,
            "mgmtStdTotals": mgmt_stds,
            "costRequestLabels": np.array(cost_request_labels, dtype=object),
            "costMechanismLabels": np.array(cost_mechanism_labels, dtype=object),
            "gasValues": gas_values,
            "recordValues": record_values,
        },
    )

    export_rows = []
    for label, mechanism, request_class in intra_specs + cross_specs + mgmt_specs:
        row = get_row(df, mechanism, request_class)
        export_rows.append(
            {
                "label": label,
                "mechanism": mechanism,
                "requestClass": request_class,
                "meanMs": row["totalServiceMs_mean"],
                "stdMs": row["totalServiceMs_std"],
                "p50Ms": row["totalServiceMs_p50"],
                "p95Ms": row["totalServiceMs_p95"],
                "varianceMs2": row["totalServiceMs_variance"],
                "madMs": row["totalServiceMs_mad"],
            }
        )
    pd.DataFrame(export_rows).to_csv(LATENCY_CSV, index=False)
    print(f"Saved {DATA_FILE}")
    print(f"Saved {LATENCY_CSV}")
    print(f"Source run: {RUN_DIR}")


if __name__ == "__main__":
    main()
