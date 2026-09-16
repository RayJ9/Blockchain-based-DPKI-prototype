from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "figure_data.csv"
XCOL = "epsilon"
SERIES = [
    ("DPKI_upper_bound", "DPKI Upper Bound", "-", "#008000", None),
    ("DPKI_lower_bound", "DPKI Lower Bound", "-", "#0072bd", None),
    ("DPKI_experimental", "DPKI Experimental", "--", "#ff6a00", "o"),
    ("PKI_theory", "PKI Theory", "-", "#d90404", None),
    ("PKI_experimental", "PKI Experimental", "", "#d90404", "D"),
]


def main() -> None:
    df = pd.read_csv(DATA)
    curve = df[df["dataKind"] == "measured_point"].sort_values(XCOL)
    points = df[df["dataKind"] == "measured_point"].sort_values(XCOL)

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for col, label, style, color, marker in SERIES:
        if col not in df.columns:
            continue
        curve_part = curve[[XCOL, col]].dropna()
        if style and not curve_part.empty:
            ax.plot(curve_part[XCOL], curve_part[col], style, color=color, linewidth=1.8, label=label)
        point_part = points[[XCOL, col]].dropna()
        if marker and not point_part.empty:
            ax.plot(
                point_part[XCOL],
                point_part[col],
                marker,
                linestyle="none",
                markerfacecolor="none",
                markeredgewidth=1.4,
                color=color,
                markersize=4.5,
                label=label if not style else label.replace(" Trend", ""),
            )

    ax.set_xlabel(r"$\epsilon$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.grid(True, linestyle="--", alpha=0.55)
    ax.legend(fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(ROOT / "figure.png", dpi=300)
    fig.savefig(ROOT / "figure.eps", format="eps")


if __name__ == "__main__":
    main()
