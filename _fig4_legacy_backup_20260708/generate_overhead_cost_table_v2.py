from pathlib import Path

import math
import pandas as pd


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "prototype_baseline_benchmark" / "outputs"


def pick_run_dir() -> Path:
    candidates = list(RUN_ROOT.glob("actual_overhead_stagebreakdown_onegroup_*"))
    if not candidates:
        candidates = list(RUN_ROOT.glob("actual_overhead*_onegroup_*"))
    if not candidates:
        raise FileNotFoundError("No actual overhead run found.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


RUN_DIR = pick_run_dir()
SUMMARY = pd.read_csv(RUN_DIR / "summary_by_request_class.csv")


MECHANISM_LABELS = {
    "proposed-dpki": "Our proposed DPKI",
    "traditional-pki": "Centralized PKI",
    "threshold-validation-dpki": "Multi-CA based DPKI",
    "full-contract-onchain": "full-contract DPKI",
}

REQUEST_LABELS = {
    ("proposed-dpki", "management"): "Mgmt.",
    ("proposed-dpki", "intra-off-chain"): "Intra-off",
    ("proposed-dpki", "intra-on-chain"): "Intra-on",
    ("proposed-dpki", "cross-on-chain"): "Cross",
    ("traditional-pki", "management"): "Mgmt.",
    ("traditional-pki", "intra-auth"): "Intra",
    ("traditional-pki", "cross-auth"): "Cross",
    ("threshold-validation-dpki", "management"): "Mgmt.",
    ("threshold-validation-dpki", "intra-auth"): "Intra",
    ("threshold-validation-dpki", "cross-auth"): "Cross",
    ("full-contract-onchain", "management"): "Mgmt.",
    ("full-contract-onchain", "intra-on-chain"): "Intra-on",
    ("full-contract-onchain", "cross-on-chain"): "Cross",
}

MECHANISM_ORDER = {
    "proposed-dpki": 0,
    "traditional-pki": 1,
    "threshold-validation-dpki": 2,
    "full-contract-onchain": 3,
}

REQUEST_ORDER = {
    "management": 0,
    "intra-off-chain": 1,
    "intra-on-chain": 2,
    "intra-auth": 3,
    "cross-on-chain": 4,
    "cross-auth": 5,
}


def fmt_num(value: object, digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    numeric = float(value)
    if abs(numeric - round(numeric)) < 0.05:
        return str(int(round(numeric)))
    return f"{numeric:.{digits}f}"


def build_table() -> pd.DataFrame:
    ordered = SUMMARY.sort_values(
        by=["mechanism", "requestClass"],
        key=lambda series: series.map(
            lambda value: MECHANISM_ORDER.get(value, 999)
            if series.name == "mechanism"
            else REQUEST_ORDER.get(value, 999)
        ),
    )

    rows = []
    for _, row in ordered.iterrows():
        mechanism = row["mechanism"]
        request_class = row["requestClass"]

        gas_used = float(row["gasUsed_mean"])
        raw_tx = float(row["rawTxBytes_mean"])
        receipt_log = float(row["receiptLogBytes_mean"])
        onchain_storage = raw_tx + receipt_log if gas_used > 0 else math.nan
        gas_k = gas_used / 1000.0 if gas_used > 0 else math.nan
        internal_coord = float(row["thresholdInternalPayloadBytes_mean"])
        if internal_coord < 0.5:
            internal_coord = math.nan

        rows.append(
            {
                "Mechanism": MECHANISM_LABELS[mechanism],
                "Request": REQUEST_LABELS[(mechanism, request_class)],
                "External payload B": float(row["externalPayloadBytes_mean"]),
                "On-chain storage B": onchain_storage,
                "Gas (10^3)": gas_k,
                "Internal coordination B": internal_coord,
            }
        )

    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> list[str]:
    out = frame.copy()
    for column in out.columns:
        if column not in {"Mechanism", "Request"}:
            out[column] = out[column].map(fmt_num)
    columns = list(out.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in out.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return lines


def write_markdown(frame: pd.DataFrame) -> None:
    lines = ["# Resource Overhead Table V2", ""]
    lines.extend(markdown_table(frame))
    lines.extend(
        [
            "",
            "All rows come from the latest one-group actual overhead run with stage-level payload breakdown.",
            "External payload counts only externally transmitted protocol bytes.",
            "Internal coordination is reported only for Multi-CA based DPKI and is separated from the user-facing payload columns.",
        ]
    )
    (ROOT / "overhead_cost_table_v2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(frame: pd.DataFrame) -> None:
    rows = []
    previous_mechanism = None
    for _, row in frame.iterrows():
        mechanism = str(row["Mechanism"])
        mechanism_cell = mechanism if mechanism != previous_mechanism else ""
        previous_mechanism = mechanism
        rows.append(
            " & ".join(
                [
                    mechanism_cell,
                    str(row["Request"]),
                    fmt_num(row["External payload B"]),
                    fmt_num(row["On-chain storage B"]),
                    fmt_num(row["Gas (10^3)"]),
                    fmt_num(row["Internal coordination B"]),
                ]
            )
            + r" \\"
        )

    latex = r"""\begin{table*}[t]
\centering
\caption{Measured non-latency overhead of different authentication mechanisms.}
\label{tab:resource-overhead-v2}
\scriptsize
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{llrrrr}
\hline
Mechanism & Request & External payload (B) & On-chain storage (B) & Gas ($10^3$) & Internal coordination (B) \\
\hline
""" + "\n".join(rows) + r"""
\hline
\multicolumn{6}{l}{\footnotesize External payload counts only externally transmitted protocol bytes.}\\
\multicolumn{6}{l}{\footnotesize Internal coordination is separated from the main user-facing columns and is only applicable to Multi-CA based DPKI.}
\end{tabular}
\end{table*}
"""
    (ROOT / "overhead_cost_table_v2.tex").write_text(latex, encoding="utf-8")


def main() -> None:
    table = build_table()
    table.to_csv(ROOT / "overhead_cost_table_v2.csv", index=False)
    write_markdown(table)
    write_latex(table)
    print(f"Source run: {RUN_DIR}")
    print(f"Saved {ROOT / 'overhead_cost_table_v2.csv'}")
    print(f"Saved {ROOT / 'overhead_cost_table_v2.md'}")
    print(f"Saved {ROOT / 'overhead_cost_table_v2.tex'}")


if __name__ == "__main__":
    main()
