from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
MGMT = pd.read_csv(ROOT / "overhead_payload_management_v4.csv")
INTRA = pd.read_csv(ROOT / "overhead_payload_intra_v4.csv")
CROSS = pd.read_csv(ROOT / "overhead_payload_cross_v4.csv")


def short_label(text: str) -> str:
    mapping = {
        "Our proposed DPKI": "Proposed",
        "Our proposed DPKI (off-chain)": "Proposed\n(off)",
        "Our proposed DPKI (on-chain)": "Proposed\n(on)",
        "Centralized PKI": "PKI",
        "Multi-CA based DPKI": "Multi-CA",
        "full-contract DPKI": "Full-contract",
    }
    return mapping.get(text, text)


def annotate_bar(ax: plt.Axes, xs, vals, color: str, dy: float) -> None:
    for x, v in zip(xs, vals):
        if np.isnan(v) or v <= 0:
            continue
        ax.text(
            x,
            v + dy,
            f"{int(round(v))}" if abs(v - round(v)) < 0.05 else f"{v:.1f}",
            ha="center",
            va="bottom",
            fontsize=11.2,
            fontweight="bold",
            color=color,
            family="Times New Roman",
        )


def draw_panel(ax: plt.Axes, frame: pd.DataFrame, title: str) -> None:
    labels = [short_label(v) for v in frame["Scheme"]]
    payload = frame["External payload B"].to_numpy(dtype=float)

    x = np.arange(len(labels), dtype=float)
    bar_color = "#6F8FBF"

    ax.bar(
        x,
        payload,
        width=0.56,
        color=bar_color,
        edgecolor="#4A4A4A",
        linewidth=0.7,
        zorder=3,
    )

    ax.set_title(title, fontsize=15, fontweight="bold", family="Times New Roman", pad=10)
    ax.set_ylabel("External payload (B)", fontsize=13.5, fontweight="bold", family="Times New Roman")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12.2, family="Times New Roman")
    ax.tick_params(axis="y", labelsize=12.0, width=1.2, length=6)
    ax.tick_params(axis="x", width=1.2, length=6)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.7, alpha=0.85, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(-0.6, len(labels) - 0.4)

    ymax = float(np.nanmax(payload))
    ax.set_ylim(0, ymax * 1.24 + 80)
    annotate_bar(ax, x, payload, "#2D3E63", dy=max(ymax * 0.018, 22))

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 11,
            "axes.unicode_minus": False,
        }
    )

    fig, axes = plt.subplots(3, 1, figsize=(10.2, 9.8), dpi=300)

    draw_panel(axes[0], MGMT, "Management")
    draw_panel(axes[1], INTRA, "Intra-domain Authentication")
    draw_panel(axes[2], CROSS, "Cross-domain Authentication")

    fig.subplots_adjust(left=0.10, right=0.98, top=0.97, bottom=0.07, hspace=0.43)

    for suffix in ("png", "pdf", "eps"):
        fig.savefig(ROOT / f"figure_overhead_metrics_v1.{suffix}", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    main()
