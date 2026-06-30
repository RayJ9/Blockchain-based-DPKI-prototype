from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


FIG_NAME = "fig4"
ROOT = Path(__file__).resolve().parent
SUMMARY_CSV = ROOT / "source_data" / "summary_by_request_class_no_authsig.csv"
DATA_FILE = ROOT / f"data_{FIG_NAME}.mat"

STAGE_COLUMNS = [
    "meanIssueUpdateMs",
    "meanStatusValidationMs",
    "meanCertVerificationMs",
    "meanContractExecutionMs",
]


def get_row(df: pd.DataFrame, mechanism: str, request_class: str) -> pd.Series:
    rows = df[(df["mechanism"] == mechanism) & (df["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def panel(df: pd.DataFrame, specs: list[tuple[str, str, str]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    labels = []
    stages = []
    totals = []
    for label, mechanism, request_class in specs:
        row = get_row(df, mechanism, request_class)
        labels.append(label)
        stages.append([float(row[col]) for col in STAGE_COLUMNS])
        totals.append(float(row["meanNormalizedLatencyMs"]))
    return np.array(labels, dtype=object).reshape(-1, 1), np.array(stages, dtype=float), np.array(totals, dtype=float).reshape(-1, 1)


def cost_panel(df: pd.DataFrame, column: str) -> np.ndarray:
    specs = [
        ("management", "management", "management"),
        ("intra-on-chain", "intra-on-chain", "intra-on-chain"),
        ("cross-on-chain", "cross-on-chain", "cross-on-chain"),
    ]
    mechanisms = ["proposed-dpki", "ocsp-onchain-baseline", "full-contract-onchain"]
    values = np.zeros((len(specs), len(mechanisms)), dtype=float)
    for r, (_, dpki_class, other_class) in enumerate(specs):
        for c, mechanism in enumerate(mechanisms):
            request_class = dpki_class if mechanism == "proposed-dpki" else other_class
            values[r, c] = float(get_row(df, mechanism, request_class)[column])
    return values


def main() -> None:
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Missing source CSV: {SUMMARY_CSV}")
    df = pd.read_csv(SUMMARY_CSV)

    mgmt_labels, mgmt_stages, mgmt_totals = panel(
        df,
        [
            ("DPKI", "proposed-dpki", "management"),
            ("PKI", "traditional-pki", "management"),
            ("OCSP-On", "ocsp-onchain-baseline", "management"),
            ("Contract", "full-contract-onchain", "management"),
        ],
    )
    intra_labels, intra_stages, intra_totals = panel(
        df,
        [
            ("DPKI-Off", "proposed-dpki", "intra-off-chain"),
            ("PKI", "traditional-pki", "intra-auth"),
            ("DPKI-On", "proposed-dpki", "intra-on-chain"),
            ("OCSP-On", "ocsp-onchain-baseline", "intra-on-chain"),
            ("Contract", "full-contract-onchain", "intra-on-chain"),
        ],
    )
    cross_labels, cross_stages, cross_totals = panel(
        df,
        [
            ("PKI", "traditional-pki", "cross-auth"),
            ("DPKI-On", "proposed-dpki", "cross-on-chain"),
            ("OCSP-On", "ocsp-onchain-baseline", "cross-on-chain"),
            ("Contract", "full-contract-onchain", "cross-on-chain"),
        ],
    )

    gas_values = cost_panel(df, "meanGasUsed") / 1000.0
    storage_values = cost_panel(df, "meanStateWriteBytesEstimated")

    status_values = np.array(
        [
            [
                get_row(df, "proposed-dpki", "intra-on-chain")["meanStatusValidationMs"],
                get_row(df, "traditional-pki", "intra-auth")["meanStatusValidationMs"],
                get_row(df, "ocsp-onchain-baseline", "intra-on-chain")["meanStatusValidationMs"],
            ],
            [
                get_row(df, "proposed-dpki", "cross-on-chain")["meanStatusValidationMs"],
                get_row(df, "traditional-pki", "cross-auth")["meanStatusValidationMs"],
                get_row(df, "ocsp-onchain-baseline", "cross-on-chain")["meanStatusValidationMs"],
            ],
        ],
        dtype=float,
    )

    savemat(
        DATA_FILE,
        {
            "stageNames": np.array(["Issue/update", "Status", "Certificate", "Contract"], dtype=object).reshape(-1, 1),
            "stageColors": np.array(
                [
                    [245, 219, 182],
                    [200, 212, 233],
                    [218, 207, 229],
                    [245, 151, 144],
                ],
                dtype=float,
            )
            / 255.0,
            "mechanismColors": np.array(
                [
                    [158, 170, 209],
                    [245, 219, 182],
                    [245, 151, 144],
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
            "costRequestLabels": np.array(["Mgmt", "Intra", "Cross"], dtype=object).reshape(-1, 1),
            "costMechanismLabels": np.array(["DPKI-On", "OCSP-On", "Contract"], dtype=object).reshape(-1, 1),
            "gasValues": gas_values,
            "storageValues": storage_values,
            "statusRequestLabels": np.array(["Intra", "Cross"], dtype=object).reshape(-1, 1),
            "statusMechanismLabels": np.array(["MPT", "PKI-OCSP", "OCSP-On"], dtype=object).reshape(-1, 1),
            "statusValues": status_values,
        },
    )
    print(f"Saved {DATA_FILE}")


if __name__ == "__main__":
    main()
