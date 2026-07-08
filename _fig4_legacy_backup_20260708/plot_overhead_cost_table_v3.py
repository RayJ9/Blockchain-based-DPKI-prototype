from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
MGMT = pd.read_csv(ROOT / "overhead_payload_management_v3.csv")
INTRA = pd.read_csv(ROOT / "overhead_payload_intra_v3.csv")
CROSS = pd.read_csv(ROOT / "overhead_payload_cross_v3.csv")
PRIMITIVE = pd.read_csv(ROOT / "overhead_primitive_cost_v3.csv")


def fmt_cell(value: object) -> str:
    if isinstance(value, str):
        return value
    numeric = float(value)
    if abs(numeric - round(numeric)) < 0.05:
        return str(int(round(numeric)))
    return f"{numeric:.1f}"


def draw_table(ax: plt.Axes, frame: pd.DataFrame, title: str, font_size: int = 7.5) -> None:
    ax.axis("off")
    ax.text(
        0.0,
        1.03,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=font_size + 1,
        fontweight="bold",
        family="Times New Roman",
    )

    display = frame.map(fmt_cell)
    table = ax.table(
        cellText=display.values,
        colLabels=list(display.columns),
        cellLoc="center",
        colLoc="center",
        loc="upper left",
        bbox=[0.0, 0.0, 1.0, 0.95],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)

    for (row, col), cell in table.get_celld().items():
        cell.set_linewidth(0.45)
        cell.set_edgecolor("#666666")
        cell.get_text().set_family("Times New Roman")
        if row == 0:
            cell.set_facecolor("#D9EAF7")
            cell.get_text().set_fontweight("bold")
        elif col == 0:
            cell.set_facecolor("#F4F7FA")
        else:
            cell.set_facecolor("white")

    table.auto_set_column_width(col=list(range(len(display.columns))))


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 8,
            "axes.unicode_minus": False,
        }
    )

    fig = plt.figure(figsize=(8.6, 9.2), dpi=300)
    gs = fig.add_gridspec(
        4,
        1,
        height_ratios=[1.45, 1.75, 1.45, 1.65],
        left=0.02,
        right=0.98,
        top=0.98,
        bottom=0.03,
        hspace=0.22,
    )

    draw_table(fig.add_subplot(gs[0, 0]), MGMT, "Management external payload")
    draw_table(fig.add_subplot(gs[1, 0]), INTRA, "Intra-domain authentication external payload")
    draw_table(fig.add_subplot(gs[2, 0]), CROSS, "Cross-domain authentication external payload")
    draw_table(fig.add_subplot(gs[3, 0]), PRIMITIVE, "On-chain primitive cost summary")

    for suffix in ("png", "pdf", "eps"):
        fig.savefig(ROOT / f"figure_overhead_table_v3.{suffix}", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    main()
