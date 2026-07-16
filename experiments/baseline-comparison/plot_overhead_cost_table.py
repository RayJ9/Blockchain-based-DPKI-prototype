from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "overhead_cost_table.csv"


def fmt_cell(value: object) -> str:
    if isinstance(value, str):
        return value
    if pd.isna(value):
        return "-"
    numeric = float(value)
    if abs(numeric - round(numeric)) < 0.05:
        return str(int(round(numeric)))
    return f"{numeric:.0f}"


def compact_request_names(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    previous = None
    labels = []
    for value in out["Request"]:
        labels.append(value if value != previous else "")
        previous = value
    out["Request"] = labels
    return out


def main() -> None:
    frame = pd.read_csv(CSV_PATH)
    display = compact_request_names(frame).map(fmt_cell)

    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 8,
            "axes.unicode_minus": False,
        }
    )

    fig, ax = plt.subplots(figsize=(11.2, 5.8), dpi=300)
    ax.axis("off")
    ax.text(
        0.0,
        0.975,
        "Communication, storage, and gas overhead",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10.5,
        fontweight="bold",
        family="Times New Roman",
    )

    table = ax.table(
        cellText=display.values,
        colLabels=list(display.columns),
        cellLoc="center",
        colLoc="center",
        loc="upper left",
        bbox=[0.0, 0.05, 1.0, 0.90],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.2)

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
        "Communication payload and storage are reported in byte; storage denotes the persistent scheme state after completion.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.0,
        family="Times New Roman",
    )

    for suffix in ("png", "pdf", "eps"):
        fig.savefig(ROOT / f"figure_overhead_table.{suffix}", bbox_inches="tight", pad_inches=0)
    plt.close(fig)


if __name__ == "__main__":
    main()
