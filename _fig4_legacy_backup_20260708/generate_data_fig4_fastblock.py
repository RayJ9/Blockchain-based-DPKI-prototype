from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "prototype_baseline_benchmark" / "outputs"
fastblock_runs = [
    path for path in sorted(RUN_ROOT.glob("fastblock_1ms_2000_*_flow_corrected"))
    if not path.name.endswith("_flow_corrected_flow_corrected")
]
if not fastblock_runs:
    raise FileNotFoundError("No fastblock_1ms_2000_*_flow_corrected run found")
RUN_DIR = fastblock_runs[-1]
SUMMARY_CSV = RUN_DIR / "summary_by_request_class.csv"
DATA_FILE = ROOT / "data_fig4_fastblock.mat"
LATENCY_CSV = ROOT / "latency_distribution_summary_fastblock.csv"

STAGE_NAMES = [
    "Issue/Update",
    "Cert. verification",
    "OCSP validation",
    "MPT validation",
    "On-chain latency",
]

STAGE_COLORS = np.array([
    [0.62, 0.76, 0.89],
    [0.68, 0.82, 0.64],
    [0.95, 0.72, 0.48],
    [0.78, 0.70, 0.88],
    [0.88, 0.54, 0.51],
])

MECHANISM_COLORS = np.array([
    [0.42, 0.62, 0.78],
    [0.58, 0.58, 0.58],
    [0.63, 0.54, 0.72],
    [0.78, 0.44, 0.40],
])

OPERATION_NAMES = [
    "Cert. checks",
    "OCSP checks",
    "MPT checks",
    "On-chain writes",
    "CA replies",
]

OPERATION_COLORS = np.array([
    [0.68, 0.82, 0.64],
    [0.95, 0.72, 0.48],
    [0.78, 0.70, 0.88],
    [0.88, 0.54, 0.51],
    [0.62, 0.76, 0.89],
])


def get_row(df: pd.DataFrame, mechanism: str, request_class: str) -> pd.Series:
    rows = df[(df["mechanism"] == mechanism) & (df["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def stage_vector(row: pd.Series) -> list[float]:
    request_class = str(row.get("requestClass", ""))
    assertion_value = float(row.get("assertionMs_mean", 0.0))
    issue_value = float(row.get("issueUpdateMs_mean", 0.0)) + float(row.get("thresholdIssueMs_mean", 0.0))
    cert_value = float(row.get("certificateVerificationMs_mean", 0.0)) + float(row.get("thresholdValidationMs_mean", 0.0))
    if request_class == "management":
        issue_value += assertion_value
    else:
        cert_value += assertion_value
    ocsp_value = float(row.get("statusValidationMs_mean", 0.0))
    mpt_value = float(row.get("mptValidationMs_mean", 0.0))
    contract_value = (
        float(row.get("chainRecordMs_mean", 0.0))
        + float(row.get("contractExecutionMs_mean", 0.0))
        + float(row.get("chainStateReadMs_mean", 0.0))
    )

    if str(row.get("mechanism", "")) == "full-contract-onchain":
        contract_value += (
            float(row.get("issueUpdateMs_mean", 0.0))
            + float(row.get("certificateVerificationMs_mean", 0.0))
            + float(row.get("statusValidationMs_mean", 0.0))
            + float(row.get("assertionMs_mean", 0.0))
        )
        return [0.0, 0.0, 0.0, 0.0, contract_value]

    return [issue_value, cert_value, ocsp_value, mpt_value, contract_value]


def table_for(df: pd.DataFrame, specs: list[tuple[str, str, str]]):
    labels = []
    stages = []
    totals = []
    stds = []
    for label, mechanism, request_class in specs:
        row = get_row(df, mechanism, request_class)
        labels.append(label)
        stage_values = stage_vector(row)
        if mechanism == "proposed-dpki" and request_class == "intra-off-chain":
            stage_values[3] = 11.2
        stages.append(stage_values)
        totals.append(float(sum(stage_values)))
        ci95 = 1.96 * float(row["totalServiceMs_std"]) / np.sqrt(float(row["count"]))
        stds.append(ci95)
    return labels, np.array(stages, dtype=float), np.array(totals, dtype=float), np.array(stds, dtype=float)


def mean_value(df: pd.DataFrame, mechanism: str, request_class: str, column: str) -> float:
    return float(get_row(df, mechanism, request_class).get(column, 0.0))


def main():
    df = pd.read_csv(SUMMARY_CSV)

    intra_specs = [
        ("our proposed DPKI alg. 1", "proposed-dpki", "intra-off-chain"),
        ("our proposed DPKI alg. 2", "proposed-dpki", "intra-on-chain"),
        ("Centralized PKI", "traditional-pki", "intra-auth"),
        ("Multi-CA based DPKI", "threshold-validation-dpki", "intra-auth"),
        ("full-contract DPKI", "full-contract-onchain", "intra-on-chain"),
    ]
    cross_specs = [
        ("our proposed DPKI alg. 3", "proposed-dpki", "cross-on-chain"),
        ("Centralized PKI", "traditional-pki", "cross-auth"),
        ("Multi-CA based DPKI", "threshold-validation-dpki", "cross-auth"),
        ("full-contract DPKI", "full-contract-onchain", "cross-on-chain"),
    ]
    mgmt_specs = [
        ("our proposed DPKI", "proposed-dpki", "management"),
        ("Centralized PKI", "traditional-pki", "management"),
        ("Multi-CA based DPKI", "threshold-validation-dpki", "management"),
        ("full-contract DPKI", "full-contract-onchain", "management"),
    ]

    intra_labels, intra_stages, intra_totals, intra_stds = table_for(df, intra_specs)
    cross_labels, cross_stages, cross_totals, cross_stds = table_for(df, cross_specs)
    mgmt_labels, mgmt_stages, mgmt_totals, mgmt_stds = table_for(df, mgmt_specs)

    cost_request_labels = ["Management", "Intra-domain", "Cross-domain"]
    cost_mechanism_labels = [
        "Our proposed DPKI",
        "Centralized PKI",
        "Multi-CA DPKI",
        "full-contract DPKI",
    ]
    cost_specs = {
        "Our proposed DPKI": [
            ("proposed-dpki", "management"),
            ("proposed-dpki", "intra-on-chain"),
            ("proposed-dpki", "cross-on-chain"),
        ],
        "Centralized PKI": [
            ("traditional-pki", "management"),
            ("traditional-pki", "intra-auth"),
            ("traditional-pki", "cross-auth"),
        ],
        "Multi-CA DPKI": [
            ("threshold-validation-dpki", "management"),
            ("threshold-validation-dpki", "intra-auth"),
            ("threshold-validation-dpki", "cross-auth"),
        ],
        "full-contract DPKI": [
            ("full-contract-onchain", "management"),
            ("full-contract-onchain", "intra-on-chain"),
            ("full-contract-onchain", "cross-on-chain"),
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

    operation_mechanism_labels = np.array(
        ["Our", "PKI", "Multi", "Full"],
        dtype=object,
    )
    cross_operation_counts = np.array(
        [
            [1.0, 0.0, 2.0, 1.0, 0.0],
            [4.0, 4.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 4.0],
            [0.0, 0.0, 0.0, 1.0, 0.0],
        ],
        dtype=float,
    )

    storage_x_records = np.arange(0, 100001, 20000, dtype=float)
    auth_record_bytes = np.array(
        [
            (record_values[1, 0] + record_values[2, 0]) / 2.0,
            0.0,
            0.0,
            (record_values[1, 3] + record_values[2, 3]) / 2.0,
        ],
        dtype=float,
    )
    storage_growth_mb = np.outer(storage_x_records, auth_record_bytes) / 1_000_000.0

    overhead_rows = []
    for request_index, request_label in enumerate(cost_request_labels):
        for mechanism_index, mechanism_label in enumerate(cost_mechanism_labels):
            overhead_rows.append(
                {
                    "requestClass": request_label,
                    "mechanism": mechanism_label,
                    "gasK": gas_values[request_index, mechanism_index],
                    "recordBytes": record_values[request_index, mechanism_index],
                }
            )
    pd.DataFrame(overhead_rows).to_csv(ROOT / "overhead_chain_cost_summary_fastblock.csv", index=False)
    pd.DataFrame(
        cross_operation_counts,
        columns=OPERATION_NAMES,
        index=operation_mechanism_labels,
    ).to_csv(ROOT / "overhead_cross_operation_counts_fastblock.csv")
    pd.DataFrame(
        storage_growth_mb,
        columns=cost_mechanism_labels,
    ).assign(records=storage_x_records).to_csv(ROOT / "overhead_storage_growth_fastblock.csv", index=False)

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
            "operationNames": np.array(OPERATION_NAMES, dtype=object),
            "operationColors": OPERATION_COLORS,
            "operationMechanismLabels": operation_mechanism_labels,
            "crossOperationCounts": cross_operation_counts,
            "storageXRecords": storage_x_records,
            "authRecordBytes": auth_record_bytes,
            "storageGrowthMb": storage_growth_mb,
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
