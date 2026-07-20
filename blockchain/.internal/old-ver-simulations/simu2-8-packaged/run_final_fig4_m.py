from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

from real_sweep_figures import BASE, SWEEP_ROOT, RunSpec, fmt_value, read_run_point, run_real_experiment
from run_final_first_three import OUT_DIR, restart_pow, smooth_curve, finite_xy


M_VALUES = [2, 3, 4, 5, 6, 7, 8]
M_LAMBDA_ARRIVAL = 6.0
MEAN_BLOCK_MS = 20


def run_or_reuse(spec: RunSpec, skip_existing: bool) -> Path:
    run_dir = SWEEP_ROOT / spec.sweep / spec.label
    if skip_existing and (run_dir / "real_calibrated_params.json").exists():
        print(f"reuse {spec.sweep}:{spec.label}", flush=True)
        return run_dir
    print(f"run {spec.sweep}:{spec.label}", flush=True)
    return run_real_experiment(spec)


def plot_fig4(points: pd.DataFrame) -> None:
    dense_x = np.linspace(points["M"].min(), points["M"].max(), 260)
    smooth = pd.DataFrame({"M": dense_x})
    series = [
        ("DPKI_upper_theory", "DPKI Upper Bound", "--", (0.0, 0.5, 0.0), 2),
        ("DPKI_lower_theory", "DPKI Lower Bound", "--", (0.0, 0.447, 0.741), 2),
        ("DPKI_sim", "DPKI Experimental", "-", (1.0, 0.4, 0.0), 2),
        ("PKI_theory", "PKI Theory", "--", (0.85, 0.0, 0.0), 2),
        ("PKI_sim", "PKI Experimental", "-", (0.85, 0.0, 0.0), 2),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, label, style, color, degree in series:
        x, y = finite_xy(points, "M", column)
        if len(x) == 0:
            continue
        if len(x) == 1:
            smooth[column] = np.full_like(dense_x, y[0], dtype=float)
        else:
            smooth[column] = PchipInterpolator(x, y, extrapolate=False)(dense_x)
        ax.plot(dense_x, smooth[column], style, color=color, linewidth=1.6, label=label)
        ax.plot(x, y, "o", color=color, markersize=3.0)
    ax.set_xlabel(r"$M$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8, frameon=True, framealpha=1.0)
    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "Fig4_M_ET.png", dpi=300)
    fig.savefig(OUT_DIR / "Fig4_M_ET.eps", format="eps")
    plt.close(fig)
    points.to_csv(OUT_DIR / "Fig4_M_ET_points.csv", index=False)
    smooth.to_csv(OUT_DIR / "Fig4_M_ET_smooth.csv", index=False)


def run_fig4(args: argparse.Namespace) -> pd.DataFrame:
    restart_pow(MEAN_BLOCK_MS)
    rows: list[dict[str, float]] = []
    for index, value in enumerate(M_VALUES):
        run_dir = run_or_reuse(
            RunSpec(
                label=f"fig4_lambda6_fixedseed_M_{fmt_value(value)}",
                sweep="final_fig4_lambda6_fixedseed/M",
                x_name="M",
                x_value=float(value),
                epsilon_points=str(BASE["epsilon"]),
                requests=args.requests,
                lambda_arrival=M_LAMBDA_ARRIVAL,
                p_manage=BASE["p_manage"],
                gamma_on_chain=BASE["gamma_on_chain"],
                service_cas=int(value),
                lambda_block=BASE["lambda_block"],
                service_shape_mode="target-exponential",
                arrival_mode="virtual",
                kind_plan_mode="random",
                dpki_auth_shape_mean_ms=180.0,
                dpki_management_shape_mean_ms=260.0,
                pki_auth_shape_mean_ms=180.0,
                pki_management_shape_mean_ms=560.0,
                seed=args.seed,
            ),
            args.skip_existing,
        )
        row = read_run_point(run_dir, "M", float(value), BASE["epsilon"])
        row["runDir"] = str(run_dir)
        rows.append(row)
        pd.DataFrame(rows).to_csv(OUT_DIR / "Fig4_M_ET_points_partial.csv", index=False)
    points = pd.DataFrame(rows).sort_values("M")
    plot_fig4(points)
    return points


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run final real experiment for Fig4 M sweep.")
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=72001)
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "M_values": M_VALUES,
        "lambda_arrival": M_LAMBDA_ARRIVAL,
        "mean_block_ms": MEAN_BLOCK_MS,
        "epsilon": BASE["epsilon"],
        "p_manage": BASE["p_manage"],
        "gamma_on_chain": BASE["gamma_on_chain"],
        "requests": args.requests,
        "service_shape_mode": "target-exponential",
        "arrival_mode": "virtual",
        "kind_plan_mode": "random",
    }
    (OUT_DIR / "manifest_fig4_M.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    points = run_fig4(args)
    print(points[["M", "DPKI_sim", "PKI_sim", "DPKI_lower_theory", "DPKI_upper_theory", "PKI_theory"]].to_string(index=False), flush=True)
    print(f"wrote final Fig4 under {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
