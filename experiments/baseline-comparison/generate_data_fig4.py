from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


ROOT = Path(__file__).resolve().parent
SUMMARY_CSV = ROOT / "source_data" / "summary_by_request_class_fastblock.csv"
DATA_FILE = ROOT / "data_fig4.mat"
LATENCY_CSV = ROOT / "latency_distribution_summary.csv"

STAGE_NAMES = [
    "Packaging delay",
    "On-chain execution",
    "Issue/Update",
    "Cert. verification",
    "OCSP validation",
    "MPT validation",
]

STAGE_COLORS = np.array([
    [0.93, 0.79, 0.80],
    [0.88, 0.54, 0.51],
    [0.62, 0.76, 0.89],
    [0.68, 0.82, 0.64],
    [0.95, 0.72, 0.48],
    [0.78, 0.70, 0.88],
])

def get_row(df: pd.DataFrame, mechanism: str, request_class: str) -> pd.Series:
    rows = df[(df["mechanism"] == mechanism) & (df["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def stage_vector(row: pd.Series) -> list[float]:
    names = ["assertionMs_mean", "issueUpdateMs_mean", "thresholdIssueMs_mean",
             "certificateVerificationMs_mean", "thresholdValidationMs_mean", "statusValidationMs_mean",
             "mptValidationMs_mean", "chainRecordMs_mean", "contractExecutionMs_mean", "chainStateReadMs_mean",
             "receiptWaitMs_mean", "totalServiceMs_mean"]
    values = {name: float(row[name]) for name in names}
    if any(not np.isfinite(v) or v < 0 for v in values.values()):
        raise ValueError("Stage measurements must be finite and nonnegative")
    issue = values["issueUpdateMs_mean"] + values["thresholdIssueMs_mean"]
    cert = values["certificateVerificationMs_mean"] + values["thresholdValidationMs_mean"]
    if str(row["requestClass"]) == "management":
        issue += values["assertionMs_mean"]
    else:
        cert += values["assertionMs_mean"]
    onchain = values["chainRecordMs_mean"] + values["contractExecutionMs_mean"] + values["chainStateReadMs_mean"]
    packaging = values["receiptWaitMs_mean"]
    execution = onchain - packaging
    if execution < 0:
        raise ValueError("Measured receipt wait exceeds the recorded on-chain duration")
    stages = [packaging, execution, issue, cert, values["statusValidationMs_mean"], values["mptValidationMs_mean"]]
    if not np.isclose(sum(stages), values["totalServiceMs_mean"], rtol=1e-9, atol=1e-9):
        raise ValueError("Stage totals do not match measured totalServiceMs_mean")
    return stages


def table_for(df: pd.DataFrame, specs: list[tuple[str, str, str]]):
    labels = []
    stages = []
    totals = []
    stds = []
    for label, mechanism, request_class in specs:
        row = get_row(df, mechanism, request_class)
        labels.append(label)
        stage_values = stage_vector(row)
        stages.append(stage_values)
        totals.append(float(row["totalServiceMs_mean"]))
        ci95 = 1.96 * float(row["totalServiceMs_std"]) / np.sqrt(float(row["count"]))
        stds.append(ci95)
    return labels, np.array(stages, dtype=float), np.array(totals, dtype=float), np.array(stds, dtype=float)


def main():
    df = pd.read_csv(SUMMARY_CSV)

    intra_specs = [
        ("Our proposed DPKI alg. 1", "proposed-dpki", "intra-off-chain"),
        ("Our proposed DPKI alg. 2", "proposed-dpki", "intra-on-chain"),
        ("Centralized PKI", "traditional-pki", "intra-auth"),
        ("Multi-CA based DPKI", "threshold-validation-dpki", "intra-auth"),
        ("Full contract DPKI", "full-contract-onchain", "intra-on-chain"),
    ]
    cross_specs = [
        ("Our proposed DPKI alg. 3", "proposed-dpki", "cross-on-chain"),
        ("Centralized PKI", "traditional-pki", "cross-auth"),
        ("Multi-CA based DPKI", "threshold-validation-dpki", "cross-auth"),
        ("Full contract DPKI", "full-contract-onchain", "cross-on-chain"),
    ]
    mgmt_specs = [
        ("Our proposed DPKI", "proposed-dpki", "management"),
        ("Centralized PKI", "traditional-pki", "management"),
        ("Multi-CA based DPKI", "threshold-validation-dpki", "management"),
        ("Full contract DPKI", "full-contract-onchain", "management"),
    ]

    intra_labels, intra_stages, intra_totals, intra_stds = table_for(df, intra_specs)
    cross_labels, cross_stages, cross_totals, cross_stds = table_for(df, cross_specs)
    mgmt_labels, mgmt_stages, mgmt_totals, mgmt_stds = table_for(df, mgmt_specs)

    savemat(
        DATA_FILE,
        {
            "stageNames": np.array(STAGE_NAMES, dtype=object),
            "stageColors": STAGE_COLORS,
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
        },
    )

    export_rows = []
    for label, mechanism, request_class in intra_specs + cross_specs + mgmt_specs:
        row = get_row(df, mechanism, request_class)
        stage_values = stage_vector(row)
        export_rows.append(
            {
                "label": label,
                "mechanism": mechanism,
                "requestClass": request_class,
                "meanMs": float(row["totalServiceMs_mean"]),
                "stdMs": row["totalServiceMs_std"],
                "p50Ms": row["totalServiceMs_p50"],
                "p95Ms": row["totalServiceMs_p95"],
                "varianceMs2": row["totalServiceMs_variance"],
                "madMs": row["totalServiceMs_mad"],
                "packagingMs": stage_values[0],
                "onChainExecutionMs": stage_values[1],
                "issueUpdateMs": stage_values[2],
                "certVerificationMs": stage_values[3],
                "ocspValidationMs": stage_values[4],
                "mptValidationMs": stage_values[5],
            }
        )
    pd.DataFrame(export_rows).to_csv(LATENCY_CSV, index=False)
    print(f"Saved {DATA_FILE}")
    print(f"Saved {LATENCY_CSV}")
    print(f"Source summary: {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
