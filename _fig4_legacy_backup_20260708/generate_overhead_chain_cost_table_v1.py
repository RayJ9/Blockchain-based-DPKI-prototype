from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "prototype_baseline_benchmark" / "outputs"


def pick_run_dir() -> Path:
    candidates = list(RUN_ROOT.glob("actual_overhead_stagebreakdown_receiptgas_onegroup_*"))
    if not candidates:
        raise FileNotFoundError("No receipt-gas overhead run found.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


RUN_DIR = pick_run_dir()
SUMMARY = pd.read_csv(RUN_DIR / "summary_by_request_class.csv")


def row_lookup(mechanism: str, request_class: str) -> pd.Series:
    rows = SUMMARY[(SUMMARY["mechanism"] == mechanism) & (SUMMARY["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def storage_bytes(row: pd.Series) -> float:
    return float(row["rawTxBytes_mean"]) + float(row["receiptLogBytes_mean"])


def gas_k(row: pd.Series) -> float:
    return float(row["gasUsed_mean"]) / 1000.0


def fmt_num(value: object, digits: int = 1) -> str:
    numeric = float(value)
    if abs(numeric - round(numeric)) < 0.05:
        return str(int(round(numeric)))
    return f"{numeric:.{digits}f}"


def build_table() -> pd.DataFrame:
    proposed_mgmt = row_lookup("proposed-dpki", "management")
    proposed_intra_on = row_lookup("proposed-dpki", "intra-on-chain")
    proposed_cross = row_lookup("proposed-dpki", "cross-on-chain")
    full_intra = row_lookup("full-contract-onchain", "intra-on-chain")
    full_cross = row_lookup("full-contract-onchain", "cross-on-chain")

    return pd.DataFrame(
        [
            {
                "Primitive": "Cert/root write",
                "Applied request": "Management",
                "Used by": "Proposed Mgmt.; Multi-CA Mgmt.; full-contract Mgmt.",
                "On-chain storage B": storage_bytes(proposed_mgmt),
                "Receipt gas used (10^3)": gas_k(proposed_mgmt),
            },
            {
                "Primitive": "Auth record write + read",
                "Applied request": "Intra-domain",
                "Used by": "Proposed DPKI (on-chain)",
                "On-chain storage B": storage_bytes(proposed_intra_on),
                "Receipt gas used (10^3)": gas_k(proposed_intra_on),
            },
            {
                "Primitive": "Auth record write + read",
                "Applied request": "Cross-domain",
                "Used by": "Proposed DPKI (cross-domain)",
                "On-chain storage B": storage_bytes(proposed_cross),
                "Receipt gas used (10^3)": gas_k(proposed_cross),
            },
            {
                "Primitive": "Full-contract auth",
                "Applied request": "Intra-domain",
                "Used by": "full-contract DPKI",
                "On-chain storage B": storage_bytes(full_intra),
                "Receipt gas used (10^3)": gas_k(full_intra),
            },
            {
                "Primitive": "Full-contract auth",
                "Applied request": "Cross-domain",
                "Used by": "full-contract DPKI",
                "On-chain storage B": storage_bytes(full_cross),
                "Receipt gas used (10^3)": gas_k(full_cross),
            },
        ]
    )


def markdown_table(frame: pd.DataFrame) -> list[str]:
    out = frame.copy()
    for column in out.columns:
        if column not in {"Primitive", "Applied request", "Used by"}:
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
    lines = ["# On-chain Cost Table", ""]
    lines.extend(markdown_table(frame))
    lines.extend(
        [
            "",
            "All rows come from the latest one-group receipt-gas overhead run.",
            "The table reports chain-side storage and final receipt gas used by the actually invoked write primitive.",
            "Multi-CA internal committee coordination is excluded because it is not reflected as a chain-side primitive in the current prototype baseline.",
        ]
    )
    (ROOT / "overhead_chain_cost_table_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(frame: pd.DataFrame) -> None:
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            " & ".join(
                [
                    str(row["Primitive"]),
                    str(row["Applied request"]),
                    str(row["Used by"]),
                    fmt_num(row["On-chain storage B"]),
                    fmt_num(row["Receipt gas used (10^3)"]),
                ]
            )
            + r" \\"
        )

    latex = r"""\begin{table*}[t]
\centering
\caption{On-chain storage and final receipt gas used by the chain-side primitives in the prototype baselines.}
\label{tab:onchain-cost-v1}
\scriptsize
\setlength{\tabcolsep}{3.8pt}
\begin{tabular}{lllrr}
\hline
Primitive & Applied request & Used by & On-chain storage (B) & Receipt gas used ($10^3$) \\
\hline
""" + "\n".join(rows) + r"""
\hline
\multicolumn{5}{l}{\footnotesize Multi-CA internal committee coordination is excluded because it is not reflected as a chain-side primitive in the current prototype baseline.}
\end{tabular}
\end{table*}
"""
    (ROOT / "overhead_chain_cost_table_v1.tex").write_text(latex, encoding="utf-8")


def main() -> None:
    frame = build_table()
    frame.to_csv(ROOT / "overhead_chain_cost_table_v1.csv", index=False)
    write_markdown(frame)
    write_latex(frame)
    print(f"Source run: {RUN_DIR}")
    print(f"Saved {ROOT / 'overhead_chain_cost_table_v1.csv'}")
    print(f"Saved {ROOT / 'overhead_chain_cost_table_v1.md'}")
    print(f"Saved {ROOT / 'overhead_chain_cost_table_v1.tex'}")


if __name__ == "__main__":
    main()
