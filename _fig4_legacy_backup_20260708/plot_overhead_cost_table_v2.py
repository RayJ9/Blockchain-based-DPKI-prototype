from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "overhead_cost_table_v2.csv"


def fmt_cell(value: object) -> str:
    if isinstance(value, str):
        return value
    numeric = float(value)
    if pd.isna(numeric):
        return "-"
    if abs(numeric - round(numeric)) < 0.05:
        return str(int(round(numeric)))
    return f"{numeric:.1f}"


def compact_mechanism_names(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    previous = None
    labels = []
    for value in out["Mechanism"]:
        labels.append(value if value != previous else "")
        previous = value
    out["Mechanism"] = labels
    return out


def main() -> None:
    frame = pd.read_csv(CSV_PATH)
    display = compact_mechanism_names(frame).map(fmt_cell)

    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 8,
            "axes.unicode_minus": False,
        }
    )

    fig, ax = plt.subplots(figsize=(9.6, 5.6), dpi=300)
    ax.axis("off")
    ax.text(
        0.0,
        1.03,
        "Overhead comparison (draft v2)",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        family="Times New Roman",
    )

    table = ax.table(
        cellText=display.values,
        colLabels=list(display.columns),
        cellLoc="center",
        colLoc="center",
        loc="upper left",
        bbox=[0.0, 0.04, 1.0, 0.92],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)

    for (row, col), cell in table.get_celld().items():
        cell.set_linewidth(0.45)
        cell.set_edgecolor("#666666")
        cell.get_text().set_family("Times New Roman")
        if row == 0:
            cell.set_facecolor("#D9EAF7")
            cell.get_text().set_fontweight("bold")
        elif col in (0, 1):
            cell.set_facecolor("#F4F7FA")
        else:
            cell.set_facecolor("white")

    table.auto_set_column_width(col=list(range(len(display.columns))))

    ax.text(
        0.0,
        0.0,
        "External payload counts only externally transmitted protocol bytes. Internal coordination is separated from the main user-facing columns.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7,
        family="Times New Roman",
    )

    for suffix in ("png", "pdf", "eps"):
        fig.savefig(ROOT / f"figure_overhead_table_v2.{suffix}", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    main()
