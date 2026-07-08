from pathlib import Path

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


def row_lookup(mechanism: str, request_class: str) -> pd.Series:
    rows = SUMMARY[(SUMMARY["mechanism"] == mechanism) & (SUMMARY["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def fmt_num(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    if abs(value - round(value)) < 0.05:
        return str(int(round(value)))
    return f"{value:.{digits}f}"


def panel_df(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    records = []
    for label, mechanism, request_class in rows:
        row = row_lookup(mechanism, request_class)
        records.append(
            {
                "Scheme": label,
                "External payload B": float(row["externalPayloadBytes_mean"]),
            }
        )
    return pd.DataFrame(records)


def primitive_df() -> pd.DataFrame:
    proposed_mgmt = row_lookup("proposed-dpki", "management")
    proposed_intra_on = row_lookup("proposed-dpki", "intra-on-chain")
    full_intra = row_lookup("full-contract-onchain", "intra-on-chain")
    full_cross = row_lookup("full-contract-onchain", "cross-on-chain")

    return pd.DataFrame(
        [
            {
                "Primitive": "Cert/root write",
                "Used by": "Proposed Mgmt.; Multi-CA Mgmt.; full-contract Mgmt.",
                "On-chain storage B": float(proposed_mgmt["rawTxBytes_mean"]) + float(proposed_mgmt["receiptLogBytes_mean"]),
                "Gas (10^3)": float(proposed_mgmt["gasUsed_mean"]) / 1000.0,
            },
            {
                "Primitive": "Auth record write + read",
                "Used by": "Proposed Intra-on; Proposed Cross",
                "On-chain storage B": float(proposed_intra_on["rawTxBytes_mean"]) + float(proposed_intra_on["receiptLogBytes_mean"]),
                "Gas (10^3)": float(proposed_intra_on["gasUsed_mean"]) / 1000.0,
            },
            {
                "Primitive": "Full-contract intra auth",
                "Used by": "full-contract Intra-on",
                "On-chain storage B": float(full_intra["rawTxBytes_mean"]) + float(full_intra["receiptLogBytes_mean"]),
                "Gas (10^3)": float(full_intra["gasUsed_mean"]) / 1000.0,
            },
            {
                "Primitive": "Full-contract cross auth",
                "Used by": "full-contract Cross",
                "On-chain storage B": float(full_cross["rawTxBytes_mean"]) + float(full_cross["receiptLogBytes_mean"]),
                "Gas (10^3)": float(full_cross["gasUsed_mean"]) / 1000.0,
            },
        ]
    )


def markdown_table(frame: pd.DataFrame) -> list[str]:
    out = frame.copy()
    for column in out.columns:
        if column not in {"Scheme", "Primitive", "Used by"}:
            out[column] = out[column].map(fmt_num)
    columns = list(out.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in out.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return lines


def write_markdown(mgmt: pd.DataFrame, intra: pd.DataFrame, cross: pd.DataFrame, primitive: pd.DataFrame) -> None:
    lines = ["# Resource Overhead Table V3", ""]
    lines.extend(["## Management external payload", ""])
    lines.extend(markdown_table(mgmt))
    lines.extend(["", "## Intra-domain authentication external payload", ""])
    lines.extend(markdown_table(intra))
    lines.extend(["", "## Cross-domain authentication external payload", ""])
    lines.extend(markdown_table(cross))
    lines.extend(["", "## On-chain primitive cost summary", ""])
    lines.extend(markdown_table(primitive))
    lines.extend(
        [
            "",
            "All rows come from the latest one-group actual overhead run with stage-level payload breakdown.",
            "The external payload panels compare management with management, intra-domain with intra-domain, and cross-domain with cross-domain.",
            "Multi-CA internal committee coordination is intentionally excluded from the user-facing payload tables; its hidden coordination cost is kept only in the audit logs.",
        ]
    )
    (ROOT / "overhead_cost_table_v3.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(mgmt: pd.DataFrame, intra: pd.DataFrame, cross: pd.DataFrame, primitive: pd.DataFrame) -> None:
    def rows_for(frame: pd.DataFrame, cols: list[str]) -> str:
        out = []
        for _, row in frame.iterrows():
            parts = []
            for col in cols:
                value = row[col]
                if isinstance(value, str):
                    parts.append(value)
                else:
                    parts.append(fmt_num(float(value)))
            out.append(" & ".join(parts) + r" \\")
        return "\n".join(out)

    latex = r"""\begin{table*}[t]
\centering
\caption{Measured non-latency overhead of different authentication mechanisms, grouped by request type.}
\label{tab:resource-overhead-v3}
\scriptsize
\setlength{\tabcolsep}{4.0pt}

\begin{tabular}{lr}
\hline
\multicolumn{2}{c}{Management external payload} \\
\hline
Scheme & External payload (B) \\
\hline
""" + rows_for(mgmt, ["Scheme", "External payload B"]) + r"""
\hline
\end{tabular}
\hfill
\begin{tabular}{lr}
\hline
\multicolumn{2}{c}{Intra-domain authentication external payload} \\
\hline
Scheme & External payload (B) \\
\hline
""" + rows_for(intra, ["Scheme", "External payload B"]) + r"""
\hline
\end{tabular}
\hfill
\begin{tabular}{lr}
\hline
\multicolumn{2}{c}{Cross-domain authentication external payload} \\
\hline
Scheme & External payload (B) \\
\hline
""" + rows_for(cross, ["Scheme", "External payload B"]) + r"""
\hline
\end{tabular}

\vspace{0.6em}

\begin{tabular}{llrr}
\hline
Primitive & Used by & On-chain storage (B) & Gas ($10^3$) \\
\hline
""" + rows_for(primitive, ["Primitive", "Used by", "On-chain storage B", "Gas (10^3)"]) + r"""
\hline
\multicolumn{4}{l}{\footnotesize Multi-CA internal committee coordination is excluded from the user-facing payload panels and kept only in the audit logs.}
\end{tabular}
\end{table*}
"""
    (ROOT / "overhead_cost_table_v3.tex").write_text(latex, encoding="utf-8")


def main() -> None:
    mgmt = panel_df(
        [
            ("Our proposed DPKI", "proposed-dpki", "management"),
            ("Centralized PKI", "traditional-pki", "management"),
            ("Multi-CA based DPKI", "threshold-validation-dpki", "management"),
            ("full-contract DPKI", "full-contract-onchain", "management"),
        ]
    )
    intra = panel_df(
        [
            ("Our proposed DPKI (off-chain)", "proposed-dpki", "intra-off-chain"),
            ("Our proposed DPKI (on-chain)", "proposed-dpki", "intra-on-chain"),
            ("Centralized PKI", "traditional-pki", "intra-auth"),
            ("Multi-CA based DPKI", "threshold-validation-dpki", "intra-auth"),
            ("full-contract DPKI", "full-contract-onchain", "intra-on-chain"),
        ]
    )
    cross = panel_df(
        [
            ("Our proposed DPKI", "proposed-dpki", "cross-on-chain"),
            ("Centralized PKI", "traditional-pki", "cross-auth"),
            ("Multi-CA based DPKI", "threshold-validation-dpki", "cross-auth"),
            ("full-contract DPKI", "full-contract-onchain", "cross-on-chain"),
        ]
    )
    primitive = primitive_df()

    mgmt.to_csv(ROOT / "overhead_payload_management_v3.csv", index=False)
    intra.to_csv(ROOT / "overhead_payload_intra_v3.csv", index=False)
    cross.to_csv(ROOT / "overhead_payload_cross_v3.csv", index=False)
    primitive.to_csv(ROOT / "overhead_primitive_cost_v3.csv", index=False)
    write_markdown(mgmt, intra, cross, primitive)
    write_latex(mgmt, intra, cross, primitive)
    print(f"Source run: {RUN_DIR}")
    print(f"Saved {ROOT / 'overhead_cost_table_v3.md'}")
    print(f"Saved {ROOT / 'overhead_cost_table_v3.tex'}")


if __name__ == "__main__":
    main()
