from pathlib import Path

import math
import pandas as pd


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "prototype_baseline_benchmark" / "outputs"


def pick_run_dir() -> Path:
    candidates = list(RUN_ROOT.glob("actual_overhead_stagebreakdown_receiptgas_onegroup_*"))
    if not candidates:
        raise FileNotFoundError("No receipt-gas overhead run found.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


RUN_DIR = pick_run_dir()
METRICS = pd.read_csv(RUN_DIR / "request_metrics.csv")


def row_lookup(mechanism: str, request_class: str) -> pd.Series:
    rows = METRICS[(METRICS["mechanism"] == mechanism) & (METRICS["requestClass"] == request_class)]
    if len(rows) != 1:
        raise ValueError(f"Expected one row for {mechanism}/{request_class}, got {len(rows)}")
    return rows.iloc[0]


def int_or_none(value: float) -> int | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    numeric = float(value)
    if abs(numeric) < 0.5:
        return None
    return int(round(numeric))


def communication_bytes(row: pd.Series) -> int | None:
    return int_or_none(float(row["externalPayloadBytes"]))


def storage_bytes(row: pd.Series) -> int | None:
    mechanism = str(row["mechanism"])
    request_class = str(row["requestClass"])

    if mechanism == "traditional-pki" and request_class == "management":
        cert_bytes = int_or_none(float(row["issuedCertBytes"])) or 0
        status_bytes = int_or_none(float(row["issuedStatusBytes"])) or 0
        total = cert_bytes + status_bytes
        return total if total > 0 else None

    onchain = int_or_none(float(row["onChainStorageBytes"])) or 0
    return onchain if onchain > 0 else None


def gas_used(row: pd.Series) -> int | None:
    return int_or_none(float(row["gasUsed"]))


def build_rows() -> list[dict]:
    items = [
        ("Management", "Our proposed DPKI", "proposed-dpki", "management"),
        ("Management", "Centralized PKI", "traditional-pki", "management"),
        ("Management", "Multi-CA based DPKI", "threshold-validation-dpki", "management"),
        ("Management", "full-contract DPKI", "full-contract-onchain", "management"),
        ("Intra-domain", "Our proposed DPKI (off-chain)", "proposed-dpki", "intra-off-chain"),
        ("Intra-domain", "Our proposed DPKI (on-chain)", "proposed-dpki", "intra-on-chain"),
        ("Intra-domain", "Centralized PKI", "traditional-pki", "intra-auth"),
        ("Intra-domain", "Multi-CA based DPKI", "threshold-validation-dpki", "intra-auth"),
        ("Intra-domain", "full-contract DPKI", "full-contract-onchain", "intra-on-chain"),
        ("Cross-domain", "Our proposed DPKI", "proposed-dpki", "cross-on-chain"),
        ("Cross-domain", "Centralized PKI", "traditional-pki", "cross-auth"),
        ("Cross-domain", "Multi-CA based DPKI", "threshold-validation-dpki", "cross-auth"),
        ("Cross-domain", "full-contract DPKI", "full-contract-onchain", "cross-on-chain"),
    ]

    rows = []
    for request_label, scheme_label, mechanism, request_class in items:
        row = row_lookup(mechanism, request_class)
        rows.append(
            {
                "Request": request_label,
                "Scheme": scheme_label,
                "Communication payload (byte)": communication_bytes(row),
                "Storage (byte)": storage_bytes(row),
                "Receipt gas used": gas_used(row),
            }
        )
    return rows


def fmt_cell(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    if isinstance(value, (int, float)):
        return str(int(round(float(value))))
    return str(value)


def export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    exported = frame.copy()
    for column in exported.columns:
        if column in ("Request", "Scheme"):
            exported[column] = exported[column].astype(str)
        else:
            exported[column] = exported[column].map(
                lambda value: "" if value is None or (isinstance(value, float) and math.isnan(value)) else str(int(value))
            )
    return exported


def markdown_table(frame: pd.DataFrame) -> list[str]:
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(fmt_cell(row[column]) for column in columns) + " |")
    return lines


def write_markdown(frame: pd.DataFrame) -> None:
    lines = ["# Overhead Cost Table", ""]
    lines.extend(markdown_table(frame))
    lines.extend(
        [
            "",
            "All rows come from the latest one-group receipt-gas overhead run.",
            "Communication payload and storage are reported in byte.",
            "Storage refers only to the persistent scheme state kept after the operation completes.",
            "Gas is reported as the final receipt gas used.",
        ]
    )
    (ROOT / "overhead_cost_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(frame: pd.DataFrame) -> None:
    rows = []
    previous_request = None
    for _, row in frame.iterrows():
        request = str(row["Request"])
        request_cell = request if request != previous_request else ""
        previous_request = request
        rows.append(
            " & ".join(
                [
                    request_cell,
                    str(row["Scheme"]),
                    fmt_cell(row["Communication payload (byte)"]),
                    fmt_cell(row["Storage (byte)"]),
                    fmt_cell(row["Receipt gas used"]),
                ]
            )
            + r" \\"
        )

    latex = r"""\begin{table*}[t]
\centering
\caption{Measured communication, storage, and gas overhead of different authentication mechanisms.}
\label{tab:overhead-cost}
\scriptsize
\setlength{\tabcolsep}{4.2pt}
\begin{tabular}{llrrr}
\hline
Request & Scheme & Communication payload (byte) & Storage (byte) & Receipt gas used \\
\hline
""" + "\n".join(rows) + r"""
\hline
\multicolumn{5}{l}{\footnotesize Communication payload and storage are reported in byte.}\\
\multicolumn{5}{l}{\footnotesize Storage refers only to the persistent scheme state kept after the operation completes.}
\end{tabular}
\end{table*}
"""
    (ROOT / "overhead_cost_table.tex").write_text(latex, encoding="utf-8")


def main() -> None:
    frame = pd.DataFrame(build_rows())
    export = export_frame(frame)
    export.to_csv(ROOT / "overhead_cost_table.csv", index=False)
    write_markdown(frame)
    write_latex(frame)
    print(f"Source run: {RUN_DIR}")
    print(f"Saved {ROOT / 'overhead_cost_table.csv'}")
    print(f"Saved {ROOT / 'overhead_cost_table.md'}")
    print(f"Saved {ROOT / 'overhead_cost_table.tex'}")


if __name__ == "__main__":
    main()
