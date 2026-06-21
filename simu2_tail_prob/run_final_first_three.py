from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

from real_sweep_figures import (
    BASE,
    POW_RUNTIME,
    SCRIPT_DIR,
    SWEEP_ROOT,
    WORKSPACE_ROOT,
    RunSpec,
    build_epsilon_summary,
    fmt_value,
    read_run_point,
    run_real_experiment,
)
from simu2_cross_domain_experiment import ModelParams, pki_theory_value
from simu3_compare_cross import (
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)


OUT_DIR = SCRIPT_DIR / "final_real_figures"
FINAL_SWEEP_ROOT = SWEEP_ROOT / "final_first_three"

FIG1_EPSILON_VALUES = [round(float(x), 2) for x in np.arange(0.0, 0.6001, 0.05)]
FIG2_LAMBDA_VALUES = [4, 6, 8, 10, 12, 14, 16]
FIG2_MEAN_BLOCK_MS_VALUES = [25, 20, 15]
FIG3_P_VALUES = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]


def pow_script(name: str) -> Path:
    return WORKSPACE_ROOT / "DPKI-and-DID-platform-Lenovo" / "omnilink-pow-4nodes" / "scripts" / name


def run_powershell(script: Path, args: list[str]) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
        cwd=WORKSPACE_ROOT,
        check=True,
    )


def restart_pow(mean_block_ms: int) -> None:
    run_powershell(pow_script("stop-omnilink-pow-4nodes.ps1"), [])
    ready = POW_RUNTIME / "ready.txt"
    if ready.exists():
        ready.unlink()
    run_powershell(
        pow_script("start-omnilink-pow-4nodes.ps1"),
        ["-MeanBlockMs", str(mean_block_ms), "-MineEmpty", "-AggregateMiningOnNode0", "-WarmupSeconds", "10"],
    )
    time.sleep(30)


def epsilon_text(values: list[float]) -> str:
    return ",".join(f"{value:.2f}".rstrip("0").rstrip(".") for value in values)


def run_or_reuse(spec: RunSpec, skip_existing: bool) -> Path:
    run_dir = SWEEP_ROOT / spec.sweep / spec.label
    if skip_existing and (run_dir / "real_calibrated_params.json").exists():
        print(f"reuse {spec.sweep}:{spec.label}", flush=True)
        return run_dir
    print(f"run {spec.sweep}:{spec.label}", flush=True)
    return run_real_experiment(spec)


def finite_xy(df: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    if y_col not in df.columns:
        return np.array([]), np.array([])
    frame = df[[x_col, y_col]].dropna()
    frame = frame[np.isfinite(frame[x_col].astype(float)) & np.isfinite(frame[y_col].astype(float))]
    frame = frame.sort_values(x_col)
    return frame[x_col].astype(float).to_numpy(), frame[y_col].astype(float).to_numpy()


def smooth_curve(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray, degree: int = 3) -> np.ndarray:
    if len(x) == 0:
        return np.full_like(dense_x, np.nan, dtype=float)
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    degree = max(1, min(degree, len(x) - 1))
    try:
        coeff = np.polyfit(x, y, degree)
        return np.polyval(coeff, dense_x)
    except Exception:
        return np.interp(dense_x, x, y)


def pava(values: np.ndarray, increasing: bool = True) -> np.ndarray:
    y = values.astype(float).copy()
    if not increasing:
        y = -y
    blocks: list[tuple[float, int]] = []
    for value in y:
        blocks.append((float(value), 1))
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            v1, n1 = blocks.pop()
            v0, n0 = blocks.pop()
            merged = (v0 * n0 + v1 * n1) / (n0 + n1)
            blocks.append((merged, n0 + n1))
    out = np.array([value for value, count in blocks for _ in range(count)], dtype=float)
    return out if increasing else -out


def smooth_monotone_curve(
    x: np.ndarray,
    y: np.ndarray,
    dense_x: np.ndarray,
    increasing: bool = True,
) -> np.ndarray:
    if len(x) == 0:
        return np.full_like(dense_x, np.nan, dtype=float)
    order = np.argsort(x)
    x = x[order].astype(float)
    y = y[order].astype(float)
    unique_x = []
    unique_y = []
    for value in np.unique(x):
        mask = x == value
        unique_x.append(float(value))
        unique_y.append(float(np.mean(y[mask])))
    x = np.array(unique_x, dtype=float)
    y = pava(np.array(unique_y, dtype=float), increasing=increasing)
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    return PchipInterpolator(x, y, extrapolate=False)(dense_x)


def save_with_sources(stem: str, points: pd.DataFrame, smooth: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    points.to_csv(OUT_DIR / f"{stem}_points.csv", index=False)
    smooth.to_csv(OUT_DIR / f"{stem}_smooth.csv", index=False)


def plot_fig1(points: pd.DataFrame) -> None:
    dense_x = np.linspace(points["epsilon"].min(), points["epsilon"].max(), 300)
    smooth = pd.DataFrame({"epsilon": dense_x})
    series = [
        ("DPKI_upper_theory", "DPKI Upper Bound", "--", (0.0, 0.5, 0.0), 2),
        ("DPKI_lower_theory", "DPKI Lower Bound", "--", (0.0, 0.447, 0.741), 2),
        ("DPKI_sim", "DPKI Experimental", "-", (1.0, 0.4, 0.0), 3),
        ("PKI_theory", "PKI Theory", "--", (0.85, 0.0, 0.0), 2),
        ("PKI_sim", "PKI Experimental", "-", (0.85, 0.0, 0.0), 3),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, label, style, color, degree in series:
        x, y = finite_xy(points, "epsilon", column)
        if len(x) == 0:
            continue
        if column in {"DPKI_sim", "PKI_sim"}:
            smooth[column] = smooth_monotone_curve(x, y, dense_x, increasing=True)
        else:
            smooth[column] = smooth_curve(x, y, dense_x, degree)
        ax.plot(dense_x, smooth[column], style, color=color, linewidth=1.6, label=label)
        ax.plot(x, y, "o", color=color, markersize=3.0)
    ax.set_xlabel(r"$\epsilon$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.set_xlim(0.0, 0.6)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8, frameon=True, framealpha=1.0)
    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "Fig1_epsilon_ET.png", dpi=300)
    fig.savefig(OUT_DIR / "Fig1_epsilon_ET.eps", format="eps")
    plt.close(fig)
    save_with_sources("Fig1_epsilon_ET", points, smooth)


def lambda_group_params(group: pd.DataFrame) -> ModelParams:
    def mean_col(column: str, fallback: float) -> float:
        if column not in group.columns:
            return fallback
        values = pd.to_numeric(group[column], errors="coerce")
        values = values[np.isfinite(values)]
        return float(values.mean()) if len(values) else fallback

    return ModelParams(
        lambda_total=1.0,
        p_manage=mean_col("pManageMeasured", BASE["p_manage"]),
        q_manage=mean_col("qManageMeasured", BASE["q_manage"]),
        mu=mean_col("muModelOffchainAuthMeasured", 1.0 / 0.05),
        service_cas=int(round(mean_col("serviceCAs", BASE["service_cas"]))),
        gamma_on_chain=mean_col("gammaOnChainMeasured", BASE["gamma_on_chain"]),
        lambda_block=mean_col("lambdaBlockMeasured", BASE["lambda_block"]),
    )


def build_lambda_theory(points: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for mean_block_ms, group in points.groupby("meanBlockMs"):
        params = lambda_group_params(group)
        for lambd in np.linspace(min(FIG2_LAMBDA_VALUES), max(FIG2_LAMBDA_VALUES), 240):
            upper = theoretical_values_dpki_upper_bound(
                lambd,
                params.p_manage,
                params.q_manage,
                params.mu,
                params.service_cas,
                params.gamma_on_chain,
                params.lambda_block,
                BASE["epsilon"],
            )["E_T_total"]
            lower = theoretical_values_dpki_lower_bound(
                lambd,
                params.p_manage,
                params.q_manage,
                params.mu,
                params.service_cas,
                params.gamma_on_chain,
                params.lambda_block,
                BASE["epsilon"],
            )["E_T_total"]
            rows.append(
                {
                    "meanBlockMs": mean_block_ms,
                    "lambda": float(lambd),
                    "DPKI_upper_theory": upper,
                    "DPKI_lower_theory": lower,
                    "lambdaBlockMeasuredMean": params.lambda_block,
                }
            )
    return pd.DataFrame(rows)


def plot_fig2(points: pd.DataFrame) -> None:
    theory = build_lambda_theory(points)
    finite_exp = pd.to_numeric(points["DPKI_sim"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    y_cap = min(10.0, max(1.0, float(finite_exp.max()) * 1.12 if len(finite_exp) else 10.0))
    colors = {
        25: (0.0, 0.45, 0.74),
        20: (0.85, 0.33, 0.10),
        15: (0.47, 0.67, 0.19),
    }
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    smooth_rows: list[pd.DataFrame] = []
    for mean_block_ms in FIG2_MEAN_BLOCK_MS_VALUES:
        pts = points[points["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        curve = theory[theory["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        if pts.empty:
            continue
        measured_lp = float(pts["lambdaBlockMeasured"].mean())
        label_prefix = rf"$\lambda_p\approx{measured_lp:.1f}/s$"
        color = colors.get(mean_block_ms)
        curve = curve.replace([np.inf, -np.inf], np.nan)
        upper_curve = curve.dropna(subset=["DPKI_upper_theory"])
        lower_curve = curve.dropna(subset=["DPKI_lower_theory"])
        upper_curve = upper_curve[upper_curve["DPKI_upper_theory"] <= y_cap]
        lower_curve = lower_curve[lower_curve["DPKI_lower_theory"] <= y_cap]
        ax.plot(upper_curve["lambda"], upper_curve["DPKI_upper_theory"], "--", color=color, linewidth=1.1)
        ax.plot(lower_curve["lambda"], lower_curve["DPKI_lower_theory"], ":", color=color, linewidth=1.1)
        x, y = finite_xy(pts, "lambda", "DPKI_sim")
        dense_x = np.linspace(x.min(), x.max(), 220)
        smooth_y = smooth_monotone_curve(x, y, dense_x, increasing=True)
        smooth_rows.append(pd.DataFrame({"meanBlockMs": mean_block_ms, "lambda": dense_x, "DPKI_sim_smooth": smooth_y}))
        ax.plot(dense_x, smooth_y, "-", color=color, linewidth=1.7, label=f"{label_prefix} exp")
        ax.plot(x, y, "o", color=color, markersize=3.0)
    ax.set_xlabel(r"$\lambda$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.set_ylim(0.0, y_cap)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8, frameon=True, framealpha=1.0)
    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "Fig2_lambda_ET.png", dpi=300)
    fig.savefig(OUT_DIR / "Fig2_lambda_ET.eps", format="eps")
    plt.close(fig)
    smooth = pd.concat(smooth_rows, ignore_index=True) if smooth_rows else pd.DataFrame()
    theory.to_csv(OUT_DIR / "Fig2_lambda_ET_theory.csv", index=False)
    save_with_sources("Fig2_lambda_ET", points, smooth)


def plot_fig3(points: pd.DataFrame) -> None:
    dense_x = np.linspace(points["p"].min(), points["p"].max(), 260)
    smooth = pd.DataFrame({"p": dense_x})
    series = [
        ("DPKI_upper_theory", "DPKI Upper Bound", "--", (0.0, 0.5, 0.0), 3),
        ("DPKI_lower_theory", "DPKI Lower Bound", "--", (0.0, 0.447, 0.741), 3),
        ("DPKI_sim", "DPKI Experimental", "-", (1.0, 0.4, 0.0), 3),
        ("PKI_theory", "PKI Theory", "--", (0.85, 0.0, 0.0), 3),
        ("PKI_sim", "PKI Experimental", "-", (0.85, 0.0, 0.0), 3),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, label, style, color, degree in series:
        x, y = finite_xy(points, "p", column)
        if len(x) == 0:
            continue
        if column in {"DPKI_sim", "PKI_sim"}:
            smooth[column] = smooth_monotone_curve(x, y, dense_x, increasing=True)
        else:
            smooth[column] = smooth_curve(x, y, dense_x, degree)
        ax.plot(dense_x, smooth[column], style, color=color, linewidth=1.6, label=label)
        ax.plot(x, y, "o", color=color, markersize=3.0)
    ax.set_xlabel(r"$p$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8, frameon=True, framealpha=1.0)
    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "Fig3_p_ET.png", dpi=300)
    fig.savefig(OUT_DIR / "Fig3_p_ET.eps", format="eps")
    plt.close(fig)
    save_with_sources("Fig3_p_ET", points, smooth)


def run_fig1(args: argparse.Namespace) -> pd.DataFrame:
    restart_pow(20)
    run_dir = run_or_reuse(
        RunSpec(
            label="fig1_epsilon_0_0p6_lambdap30",
            sweep="final_first_three/fig1_epsilon",
            x_name="epsilon",
            x_value=0.0,
            epsilon_points=epsilon_text(FIG1_EPSILON_VALUES),
            requests=args.requests_epsilon,
            lambda_arrival=BASE["lambda_arrival"],
            p_manage=BASE["p_manage"],
            gamma_on_chain=BASE["gamma_on_chain"],
            service_cas=BASE["service_cas"],
            service_shape_mode=BASE["service_shape_mode"],
            arrival_mode="virtual",
            seed=args.seed,
        ),
        args.skip_existing,
    )
    points = build_epsilon_summary(run_dir)
    points.to_csv(OUT_DIR / "Fig1_epsilon_ET_points_raw.csv", index=False)
    plot_fig1(points)
    return points


def run_fig2(args: argparse.Namespace) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    try:
        for mean_index, mean_block_ms in enumerate(FIG2_MEAN_BLOCK_MS_VALUES):
            restart_pow(mean_block_ms)
            for lambda_index, lambd in enumerate(FIG2_LAMBDA_VALUES):
                run_dir = run_or_reuse(
                    RunSpec(
                        label=f"fig2_lp_ms{mean_block_ms}_lambda_{fmt_value(lambd)}",
                        sweep="final_first_three/fig2_lambda",
                        x_name="lambda",
                        x_value=float(lambd),
                        epsilon_points=str(BASE["epsilon"]),
                        requests=args.requests_lambda,
                        lambda_arrival=float(lambd),
                        p_manage=BASE["p_manage"],
                        gamma_on_chain=BASE["gamma_on_chain"],
                        service_cas=BASE["service_cas"],
                        lambda_block=1000.0 / mean_block_ms,
                        service_shape_mode=BASE["service_shape_mode"],
                        arrival_mode="virtual",
                        seed=args.seed + 10000 + mean_index * 1000 + lambda_index * 19,
                        skip_pki=True,
                    ),
                    args.skip_existing,
                )
                row = read_run_point(run_dir, "lambda", float(lambd), BASE["epsilon"])
                calibration = json.loads((run_dir / "real_calibrated_params.json").read_text(encoding="utf8"))
                row.update(
                    {
                        "meanBlockMs": mean_block_ms,
                        "configuredLambdaBlock": 1000.0 / mean_block_ms,
                        "lambdaBlockMeasurementSource": calibration.get("lambdaBlockMeasurementSource", ""),
                        "runDir": str(run_dir),
                    }
                )
                rows.append(row)
                pd.DataFrame(rows).to_csv(OUT_DIR / "Fig2_lambda_ET_points_partial.csv", index=False)
    finally:
        restart_pow(20)
    points = pd.DataFrame(rows).sort_values(["meanBlockMs", "lambda"])
    plot_fig2(points)
    return points


def run_fig3(args: argparse.Namespace) -> pd.DataFrame:
    restart_pow(20)
    rows: list[dict[str, float]] = []
    for p_value in FIG3_P_VALUES:
        run_dir = run_or_reuse(
            RunSpec(
                label=f"fig3_p_{fmt_value(p_value)}",
                sweep="final_first_three/fig3_p",
                x_name="p",
                x_value=float(p_value),
                epsilon_points=str(BASE["epsilon"]),
                requests=args.requests_p,
                lambda_arrival=BASE["lambda_arrival"],
                p_manage=float(p_value),
                gamma_on_chain=BASE["gamma_on_chain"],
                service_cas=BASE["service_cas"],
                service_shape_mode=BASE["service_shape_mode"],
                arrival_mode="virtual",
                seed=args.seed,
            ),
            args.skip_existing,
        )
        rows.append(read_run_point(run_dir, "p", float(p_value), BASE["epsilon"]))
        pd.DataFrame(rows).to_csv(OUT_DIR / "Fig3_p_ET_points_partial.csv", index=False)
    points = pd.DataFrame(rows).sort_values("p")
    plot_fig3(points)
    return points


def copy_manifest(args: argparse.Namespace) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base": BASE,
        "fig1_epsilon_values": FIG1_EPSILON_VALUES,
        "fig2_lambda_values": FIG2_LAMBDA_VALUES,
        "fig2_mean_block_ms_values": FIG2_MEAN_BLOCK_MS_VALUES,
        "fig3_p_values": FIG3_P_VALUES,
        "requests_epsilon": args.requests_epsilon,
        "requests_lambda": args.requests_lambda,
        "requests_p": args.requests_p,
        "seed": args.seed,
    }
    (OUT_DIR / "manifest_first_three.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run final real experiments for Fig1/Fig2/Fig3.")
    parser.add_argument("--only", choices=["fig1", "fig2", "fig3"], nargs="+", default=["fig1", "fig2", "fig3"])
    parser.add_argument("--requests-epsilon", type=int, default=1000)
    parser.add_argument("--requests-lambda", type=int, default=1000)
    parser.add_argument("--requests-p", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=61001)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--clean-output", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.clean_output and OUT_DIR.exists():
        for child in OUT_DIR.iterdir():
            if child.is_file():
                child.unlink()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_manifest(args)
    selected = set(args.only)
    if "fig1" in selected:
        run_fig1(args)
    if "fig2" in selected:
        run_fig2(args)
    if "fig3" in selected:
        run_fig3(args)
    print(f"wrote final first-three figures under {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
