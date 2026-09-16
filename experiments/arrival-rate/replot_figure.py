from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "figure_data.csv"
COLORS = {
    100.0: ("#4b2e83", "#b7a9d6"),
    90.0: ("#238b8d", "#9bd0d0"),
    80.0: ("#7ad63f", "#c8efad"),
}


def main() -> None:
    df = pd.read_csv(DATA)
    curve = df[df["dataKind"] == "measured_point"].copy()
    points = df[df["dataKind"] == "measured_point"].copy()

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for mean_block_ms in sorted(curve["meanBlockMs"].dropna().unique(), reverse=True):
        part = curve[curve["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        point_part = points[points["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        lambda_p = point_part["lambdaBlockMeasured"].mean()
        label_prefix = rf"$\lambda_p \approx {lambda_p:.1f}/s$" if np.isfinite(lambda_p) else rf"{mean_block_ms:.0f} ms"
        dark, light = COLORS.get(float(mean_block_ms), ("#555555", "#bbbbbb"))

        ax.plot(part["lambda"], part["DPKI_upper_bound"], "-", color=dark, linewidth=1.8, label=f"{label_prefix} upper")
        ax.plot(part["lambda"], part["DPKI_lower_bound"], "-", color=light, linewidth=1.8, label=f"{label_prefix} lower")
        ax.plot(part["lambda"], part["DPKI_experimental"], "--", color=dark, linewidth=1.8, label=f"{label_prefix} exp")
        if not point_part.empty:
            ax.plot(
                point_part["lambda"],
                point_part["DPKI_experimental"],
                "o",
                markerfacecolor="none",
                markeredgewidth=1.4,
                color=dark,
                markersize=4.2,
            )

    ax.set_xlabel(r"$\lambda$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.grid(True, linestyle="--", alpha=0.55)
    ax.legend(fontsize=7.2, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(ROOT / "figure.png", dpi=300)
    fig.savefig(ROOT / "figure.eps", format="eps")


if __name__ == "__main__":
    main()
