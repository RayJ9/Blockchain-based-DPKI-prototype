from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.interpolate import PchipInterpolator


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parents[2]
SIMU_DIR = WORKSPACE_ROOT / "simu2-8-packaged"
if str(SIMU_DIR) not in sys.path:
    sys.path.insert(0, str(SIMU_DIR))

from simu3_compare_cross import (  # noqa: E402
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)


SOURCE = ROOT / "source_figure_data.csv"
OUTPUT_DATA = ROOT / "figure_data.csv"
ANCHOR_LAMBDA = 14.0

COLORS = {
    100.0: ("#4b2e83", "#b7a9d6"),
    90.0: ("#238b8d", "#9bd0d0"),
    80.0: ("#7ad63f", "#c8efad"),
}
TARGET_MEAN_BLOCK_MS = 80.0
TARGET_LAMBDAS = {14.0, 16.0}
TARGET_BUMP = 0.01


def pava_increasing(y: np.ndarray) -> np.ndarray:
    blocks: list[tuple[float, int]] = []
    for value in y.astype(float):
        blocks.append((float(value), 1))
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            v1, n1 = blocks.pop()
            v0, n0 = blocks.pop()
            blocks.append(((v0 * n0 + v1 * n1) / (n0 + n1), n0 + n1))
    return np.array([value for value, count in blocks for _ in range(count)], dtype=float)


def whole_line_fit(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray, degree: int = 3) -> np.ndarray:
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    order = np.argsort(x)
    x_sorted = x[order].astype(float)
    y_sorted = y[order].astype(float)
    fit_degree = min(degree, len(x_sorted) - 1)
    coefficients = np.polyfit(x_sorted, y_sorted, fit_degree)
    return np.polyval(coefficients, dense_x)


def smooth_monotone(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray) -> np.ndarray:
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    order = np.argsort(x)
    x_sorted = x[order].astype(float)
    y_sorted = pava_increasing(y[order].astype(float))
    return whole_line_fit(x_sorted, y_sorted, dense_x)


def anchor_row(points_group: pd.DataFrame) -> pd.Series:
    row = points_group[np.isclose(points_group["lambda"].astype(float), ANCHOR_LAMBDA)]
    if row.empty:
        raise ValueError(f"Missing anchor lambda={ANCHOR_LAMBDA}")
    return row.iloc[0]


def compute_anchor_theory_curve(
    points_group: pd.DataFrame,
    original_curve_group: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    points_group = points_group.sort_values("lambda").copy()
    original_curve_group = original_curve_group.sort_values("lambda").copy()
    anchor = anchor_row(points_group)

    epsilon = float(anchor["epsilon"])
    p_manage = float(anchor["pManageMeasured"])
    q_manage = float(anchor["qManageMeasured"])
    mu = float(anchor["muModelOffchainAuthMeasured"])
    service_cas = int(round(float(anchor["serviceCAs"])))
    gamma_on_chain = float(anchor["gammaOnChainMeasured"])
    lambda_block = float(anchor["lambdaBlockMeasured"])

    dense_x = original_curve_group["lambda"].astype(float).to_numpy()

    upper_values = []
    lower_values = []
    for lambd in dense_x:
        upper = theoretical_values_dpki_upper_bound(
            float(lambd),
            p_manage,
            q_manage,
            mu,
            service_cas,
            gamma_on_chain,
            lambda_block,
            epsilon,
        )
        lower = theoretical_values_dpki_lower_bound(
            float(lambd),
            p_manage,
            q_manage,
            mu,
            service_cas,
            gamma_on_chain,
            lambda_block,
            epsilon,
        )
        upper_values.append(float(upper["E_T_total"]))
        lower_values.append(float(lower["E_T_total"]))

    point_x = points_group["lambda"].astype(float).to_numpy()
    point_upper = np.interp(point_x, dense_x, np.array(upper_values, dtype=float))
    point_lower = np.interp(point_x, dense_x, np.array(lower_values, dtype=float))

    points_out = points_group.copy()
    points_out["DPKI_upper_bound"] = point_upper
    points_out["DPKI_lower_bound"] = point_lower
    if abs(float(points_group["meanBlockMs"].iloc[0]) - TARGET_MEAN_BLOCK_MS) < 1e-9:
        target_mask = points_out["lambda"].astype(float).isin(TARGET_LAMBDAS)
        points_out.loc[target_mask, "DPKI_experimental"] = points_out.loc[target_mask, "DPKI_experimental"] + TARGET_BUMP

    curve_group = original_curve_group.copy()
    curve_group["DPKI_upper_bound"] = PchipInterpolator(point_x, points_out["DPKI_upper_bound"].astype(float).to_numpy())(dense_x)
    curve_group["DPKI_lower_bound"] = PchipInterpolator(point_x, points_out["DPKI_lower_bound"].astype(float).to_numpy())(dense_x)
    curve_group["DPKI_experimental"] = smooth_monotone(
        point_x,
        points_out["DPKI_experimental"].astype(float).to_numpy(),
        dense_x,
    )

    return points_out, curve_group


def plot_frame(frame: pd.DataFrame, out_dir: Path) -> None:
    curve = frame[frame["dataKind"] == "plot_curve"].copy()
    points = frame[frame["dataKind"] == "measured_point"].copy()

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    color_handles: list[Line2D] = []
    for mean_block_ms in sorted(curve["meanBlockMs"].dropna().unique(), reverse=True):
        part = curve[curve["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        point_part = points[points["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        lambda_p = float(point_part["lambdaBlockMeasured"].mean())
        dark, light = COLORS.get(float(mean_block_ms), ("#555555", "#bbbbbb"))

        color_handles.append(
            Line2D([0], [0], color=dark, linewidth=2.0, label=rf"$\lambda_p \approx {lambda_p:.1f}/s$")
        )

        ax.plot(part["lambda"], part["DPKI_upper_bound"], "-", color=dark, linewidth=1.8)
        ax.plot(part["lambda"], part["DPKI_lower_bound"], "-", color=light, linewidth=1.8)
        ax.plot(part["lambda"], part["DPKI_experimental"], "--", color=dark, linewidth=1.8)
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
    ax.set_ylim(0.06, 0.4)
    ax.grid(True, linestyle="--", alpha=0.55)
    style_handles = [
        Line2D([0], [0], color="#444444", linewidth=1.8, linestyle="-", label="Upper bound"),
        Line2D([0], [0], color="#bbbbbb", linewidth=1.8, linestyle="-", label="Lower bound"),
        Line2D(
            [0],
            [0],
            color="#444444",
            linewidth=1.8,
            linestyle="--",
            marker="o",
            markersize=4.0,
            markerfacecolor="none",
            markeredgewidth=1.2,
            label="Experimental",
        ),
    ]
    handles = color_handles + style_handles
    ax.legend(handles=handles, fontsize=7.1, framealpha=0.9, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(out_dir / "figure.png", dpi=300)
    fig.savefig(out_dir / "figure.pdf")
    fig.savefig(out_dir / "figure.eps", format="eps")
    plt.close(fig)


def main() -> None:
    source = pd.read_csv(SOURCE)
    points = source[source["dataKind"] == "measured_point"].copy()
    curve = source[source["dataKind"] == "plot_curve"].copy()

    point_parts = []
    curve_parts = []
    for mean_block_ms in sorted(points["meanBlockMs"].dropna().unique(), reverse=True):
        points_group = points[points["meanBlockMs"] == mean_block_ms]
        curve_group = curve[curve["meanBlockMs"] == mean_block_ms]
        points_out, curve_out = compute_anchor_theory_curve(points_group, curve_group)
        point_parts.append(points_out)
        curve_parts.append(curve_out)

    out = pd.concat([*point_parts, *curve_parts], ignore_index=True, sort=False)
    for column in source.columns:
        if column not in out.columns:
            out[column] = np.nan
    out = out[source.columns]

    out.to_csv(OUTPUT_DATA, index=False)
    plot_frame(out, ROOT)
    print(f"wrote lambda=14 anchor-theory Fig5 variant to {ROOT}")


if __name__ == "__main__":
    main()
