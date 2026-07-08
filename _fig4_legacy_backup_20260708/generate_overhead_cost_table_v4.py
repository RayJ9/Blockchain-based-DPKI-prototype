from pathlib import Path

import math
import pandas as pd


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "prototype_baseline_benchmark" / "outputs"


def pick_run_dir() -> Path:
    candidates = list(RUN_ROOT.glob("actual_overhead_stagebreakdown_receiptgas_onegroup_*"))
    if candidates:
        return max(candidates, key=lambda path: path.stat().st_mtime)

    candidates = list(RUN_ROOT.glob("actual_overhead_stagebreakdown_onegroup_*"))
    if not candidates:
        candidates = list(RUN_ROOT.glob("actual_overhead*_onegroup_*"))
    if not candidates:
        raise FileNotFoundError("No actual overhead run found.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


RUN_DIR = pick_run_dir()
SUMMARY = pd.read_csv(RUN_DIR / "summary_by_request_class.csv")


def row_lookup(mechanism: str, request_class: str) -> pd.Series:
    rows = SUMMARY[(SUMMARY["mechanism"] == mechanism) & (SUMMARY["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def maybe_chain_values(row: pd.Series) -> tuple[float, float]:
    gas_used = float(row["gasUsed_mean"])
    if gas_used < 0.5:
        return math.nan, math.nan
    storage = float(row["rawTxBytes_mean"]) + float(row["receiptLogBytes_mean"])
    return storage, gas_used / 1000.0


def make_row(label: str, mechanism: str, request_class: str) -> dict:
    row = row_lookup(mechanism, request_class)
    storage, gas_k = maybe_chain_values(row)
    return {
        "Scheme": label,
        "External payload B": float(row["externalPayloadBytes_mean"]),
        "On-chain storage B": storage,
        "Gas (10^3)": gas_k,
    }


def fmt_num(value: object, digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    numeric = float(value)
    if abs(numeric - round(numeric)) < 0.05:
        return str(int(round(numeric)))
    return f"{numeric:.{digits}f}"


def markdown_table(frame: pd.DataFrame) -> list[str]:
    out = frame.copy()
    for column in out.columns:
        if column != "Scheme":
            out[column] = out[column].map(fmt_num)
    columns = list(out.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in out.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return lines


def write_markdown(mgmt: pd.DataFrame, intra: pd.DataFrame, cross: pd.DataFrame) -> None:
    lines = ["# Resource Overhead Table V4", ""]
    lines.extend(["## Management comparison", ""])
    lines.extend(markdown_table(mgmt))
    lines.extend(["", "## Intra-domain authentication comparison", ""])
    lines.extend(markdown_table(intra))
    lines.extend(["", "## Cross-domain authentication comparison", ""])
    lines.extend(markdown_table(cross))
    lines.extend(
        [
            "",
            "All rows come from the latest one-group actual overhead run with stage-level payload breakdown.",
            "Each panel compares the same request type across mechanisms and reports both external payload and on-chain cost inline.",
            "Multi-CA internal committee coordination is intentionally excluded from these user-facing comparisons and kept only in the audit logs.",
            "Repeated on-chain values indicate that the corresponding schemes invoke the same chain-side write primitive under that request type.",
        ]
    )
    (ROOT / "overhead_cost_table_v4.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(mgmt: pd.DataFrame, intra: pd.DataFrame, cross: pd.DataFrame) -> None:
    def rows_for(frame: pd.DataFrame) -> str:
        out = []
        for _, row in frame.iterrows():
            out.append(
                " & ".join(
                    [
                        str(row["Scheme"]),
                        fmt_num(row["External payload B"]),
                        fmt_num(row["On-chain storage B"]),
                        fmt_num(row["Gas (10^3)"]),
                    ]
                ) + r" \\"
            )
        return "\n".join(out)

    latex = r"""\begin{table*}[t]
\centering
\caption{Measured non-latency overhead of different authentication mechanisms, grouped by request type.}
\label{tab:resource-overhead-v4}
\scriptsize
\setlength{\tabcolsep}{4.5pt}

\begin{tabular}{lrrr}
\hline
\multicolumn{4}{c}{Management comparison} \\
\hline
Scheme & External payload (B) & On-chain storage (B) & Gas ($10^3$) \\
\hline
""" + rows_for(mgmt) + r"""
\hline
\end{tabular}

\vspace{0.5em}

\begin{tabular}{lrrr}
\hline
\multicolumn{4}{c}{Intra-domain authentication comparison} \\
\hline
Scheme & External payload (B) & On-chain storage (B) & Gas ($10^3$) \\
\hline
""" + rows_for(intra) + r"""
\hline
\end{tabular}

\vspace{0.5em}

\begin{tabular}{lrrr}
\hline
\multicolumn{4}{c}{Cross-domain authentication comparison} \\
\hline
Scheme & External payload (B) & On-chain storage (B) & Gas ($10^3$) \\
\hline
""" + rows_for(cross) + r"""
\hline
\multicolumn{4}{l}{\footnotesize Multi-CA internal committee coordination is excluded from these user-facing comparisons and kept only in the audit logs.}\\
\multicolumn{4}{l}{\footnotesize Repeated on-chain values indicate that the corresponding schemes invoke the same chain-side write primitive under that request type.}
\end{tabular}
\end{table*}
"""
    (ROOT / "overhead_cost_table_v4.tex").write_text(latex, encoding="utf-8")


def main() -> None:
    mgmt = pd.DataFrame(
        [
            make_row("Our proposed DPKI", "proposed-dpki", "management"),
            make_row("Centralized PKI", "traditional-pki", "management"),
            make_row("Multi-CA based DPKI", "threshold-validation-dpki", "management"),
            make_row("full-contract DPKI", "full-contract-onchain", "management"),
        ]
    )
    intra = pd.DataFrame(
        [
            make_row("Our proposed DPKI (off-chain)", "proposed-dpki", "intra-off-chain"),
            make_row("Our proposed DPKI (on-chain)", "proposed-dpki", "intra-on-chain"),
            make_row("Centralized PKI", "traditional-pki", "intra-auth"),
            make_row("Multi-CA based DPKI", "threshold-validation-dpki", "intra-auth"),
            make_row("full-contract DPKI", "full-contract-onchain", "intra-on-chain"),
        ]
    )
    cross = pd.DataFrame(
        [
            make_row("Our proposed DPKI", "proposed-dpki", "cross-on-chain"),
            make_row("Centralized PKI", "traditional-pki", "cross-auth"),
            make_row("Multi-CA based DPKI", "threshold-validation-dpki", "cross-auth"),
            make_row("full-contract DPKI", "full-contract-onchain", "cross-on-chain"),
        ]
    )

    mgmt.to_csv(ROOT / "overhead_payload_management_v4.csv", index=False)
    intra.to_csv(ROOT / "overhead_payload_intra_v4.csv", index=False)
    cross.to_csv(ROOT / "overhead_payload_cross_v4.csv", index=False)
    write_markdown(mgmt, intra, cross)
    write_latex(mgmt, intra, cross)
    print(f"Source run: {RUN_DIR}")
    print(f"Saved {ROOT / 'overhead_cost_table_v4.md'}")
    print(f"Saved {ROOT / 'overhead_cost_table_v4.tex'}")


if __name__ == "__main__":
    main()
