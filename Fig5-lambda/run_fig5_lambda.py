from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
SIMU_DIR = WORKSPACE_ROOT / "simu2-8-packaged"
for module_dir in (SIMU_DIR, WORKSPACE_ROOT):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from real_figure_sweep_common import (  # noqa: E402
    SWEEP_ROOT,
    RunSpec,
    collect_sweep,
    fmt_value,
    mirror_final_outputs,
    parse_float_list,
    restart_pow,
    stop_pow,
    whole_line_fit,
    write_outputs,
)


def epsilon_text(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def make_specs(args: argparse.Namespace) -> list[tuple[float, RunSpec]]:
    specs: list[tuple[float, RunSpec]] = []
    for block_index, mean_block_ms in enumerate(args.mean_block_ms_values):
        for lambda_index, lambd in enumerate(args.lambda_values):
            label = (
                f"{args.tag}_blockms_{fmt_value(mean_block_ms)}"
                f"_lambda_{fmt_value(lambd)}_r{args.requests}"
            )
            specs.append(
                (
                    float(lambd),
                RunSpec(
                    label=label,
                    sweep="lambda_experiment",
                    x_name="lambda",
                    x_value=float(lambd),
                        epsilon_points=epsilon_text(args.epsilon),
                        requests=args.requests,
                        lambda_arrival=float(lambd),
                        p_manage=args.p_manage,
                        gamma_on_chain=args.gamma_on_chain,
                        q_manage=args.q_manage,
                        service_cas=args.service_cas,
                        lambda_block=1000.0 / float(mean_block_ms),
                        service_shape_mode=args.service_shape_mode,
                        arrival_mode="virtual",
                        kind_plan_mode="fixed",
                        dpki_root_read_mode=args.dpki_root_read_mode,
                        dpki_proof_read_mode=args.dpki_proof_read_mode,
                        dpki_proof_base_port=args.dpki_proof_base_port,
                        actual_execution_mode=args.actual_execution_mode,
                        dpki_auth_shape_mean_ms=args.dpki_auth_shape_mean_ms,
                        dpki_management_shape_mean_ms=args.dpki_management_shape_mean_ms,
                        pki_auth_shape_mean_ms=args.pki_auth_shape_mean_ms,
                        pki_cross_shape_mean_ms=args.pki_cross_shape_mean_ms,
                        pki_management_shape_mean_ms=args.pki_management_shape_mean_ms,
                        dpki_proof_http_mean_ms=args.dpki_proof_http_mean_ms,
                        dpki_proof_http_tail_probability=args.dpki_proof_http_tail_probability,
                        dpki_proof_http_tail_multiplier=args.dpki_proof_http_tail_multiplier,
                        dpki_auth_transfer_http_mean_ms=args.dpki_auth_transfer_http_mean_ms,
                        dpki_auth_transfer_http_tail_probability=args.dpki_auth_transfer_http_tail_probability,
                        dpki_auth_transfer_http_tail_multiplier=args.dpki_auth_transfer_http_tail_multiplier,
                        dpki_management_http_mean_ms=args.dpki_management_http_mean_ms,
                        dpki_management_http_tail_probability=args.dpki_management_http_tail_probability,
                        dpki_management_http_tail_multiplier=args.dpki_management_http_tail_multiplier,
                        dpki_management_transfer_http_mean_ms=args.dpki_management_transfer_http_mean_ms,
                        dpki_management_transfer_http_tail_probability=args.dpki_management_transfer_http_tail_probability,
                        dpki_management_transfer_http_tail_multiplier=args.dpki_management_transfer_http_tail_multiplier,
                        skip_pki=True,
                        dpki_q_mode=args.dpki_q_mode,
                        seed=args.seed + block_index * 10000 + lambda_index * 101,
                    ),
                )
            )
    return specs


def add_block_metadata(points: pd.DataFrame, tx_health: pd.DataFrame, specs: list[tuple[float, RunSpec]], args) -> None:
    meta: dict[str, dict[str, float]] = {}
    for mean_block_ms in args.mean_block_ms_values:
        for lambd in args.lambda_values:
            label = (
                f"{args.tag}_blockms_{fmt_value(mean_block_ms)}"
                f"_lambda_{fmt_value(lambd)}_r{args.requests}"
            )
            run_dir = SWEEP_ROOT / "lambda_experiment" / label
            meta[str(run_dir)] = {
                "meanBlockMs": float(mean_block_ms),
                "configuredLambdaBlock": 1000.0 / float(mean_block_ms),
            }
    for frame in (points, tx_health):
        if frame.empty or "runDir" not in frame:
            continue
        frame["meanBlockMs"] = frame["runDir"].map(lambda value: meta.get(str(value), {}).get("meanBlockMs"))
        frame["configuredLambdaBlock"] = frame["runDir"].map(
            lambda value: meta.get(str(value), {}).get("configuredLambdaBlock")
        )


def smooth_xy(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray) -> np.ndarray:
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    order = np.argsort(x)
    return whole_line_fit(x[order], y[order], dense_x)


def pava_increasing(y: np.ndarray) -> np.ndarray:
    blocks: list[tuple[float, int]] = []
    for value in y.astype(float):
        blocks.append((float(value), 1))
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            v1, n1 = blocks.pop()
            v0, n0 = blocks.pop()
            blocks.append(((v0 * n0 + v1 * n1) / (n0 + n1), n0 + n1))
    return np.array([value for value, count in blocks for _ in range(count)], dtype=float)


def smooth_monotone_xy(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray) -> np.ndarray:
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    order = np.argsort(x)
    x_sorted = x[order]
    y_sorted = pava_increasing(y[order])
    return whole_line_fit(x_sorted, y_sorted, dense_x)


def finite_series(frame: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    series = frame[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna().sort_values(x_col)
    return series[x_col].astype(float).to_numpy(), series[y_col].astype(float).to_numpy()


def lighter(color: tuple[float, ...], amount: float = 0.55) -> tuple[float, float, float]:
    return tuple(float(component + (1.0 - component) * amount) for component in color[:3])


def write_lambda_figure_data(points: pd.DataFrame, smooth: pd.DataFrame, output_dir: Path) -> None:
    rename_map = {
        "DPKI_upper_theory": "DPKI_upper_bound",
        "DPKI_lower_theory": "DPKI_lower_bound",
        "DPKI_sim": "DPKI_experimental",
    }
    raw = points.rename(columns=rename_map).copy()
    raw = raw.drop(
        columns=["PKI_sim", "PKI_theory", "PKI_rho", "pkiMuPrimaryAuthMeasured", "pkiQManageMeasured"],
        errors="ignore",
    )
    raw.insert(0, "dataKind", "measured_point")
    curve = smooth.rename(columns=rename_map).copy()
    curve.insert(0, "dataKind", "plot_curve")
    series_columns = list(rename_map.values())
    parameter_columns = [column for column in raw.columns if column not in {"dataKind", "lambda", *series_columns}]
    for column in parameter_columns:
        if column not in curve.columns:
            curve[column] = np.nan
    columns = ["dataKind", "lambda", *series_columns, *parameter_columns]
    pd.concat([raw[columns], curve[columns]], ignore_index=True).to_csv(output_dir / "figure_data.csv", index=False)


def plot_lambda(points: pd.DataFrame, output_dir: Path, prefix: str, args: argparse.Namespace) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = points.sort_values(["meanBlockMs", "lambda"]).replace([np.inf, -np.inf], np.nan)
    dense_x = np.linspace(float(frame["lambda"].min()), float(frame["lambda"].max()), 300)
    smooth_rows: list[pd.DataFrame] = []
    colors = plt.cm.viridis(np.linspace(0.12, 0.82, len(args.mean_block_ms_values)))

    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    for color, mean_block_ms in zip(colors, args.mean_block_ms_values):
        group = frame[frame["meanBlockMs"] == float(mean_block_ms)]
        if group.empty:
            continue
        lambda_p = float(pd.to_numeric(group["lambdaBlockMeasured"], errors="coerce").mean())
        label_prefix = rf"$\lambda_p\approx{lambda_p:.1f}/s$"
        out = pd.DataFrame({"lambda": dense_x, "meanBlockMs": float(mean_block_ms)})
        for column, style, label_suffix, line_color in [
            ("DPKI_upper_theory", "-", "upper", tuple(color[:3])),
            ("DPKI_lower_theory", "-", "lower", lighter(tuple(color[:3]))),
            ("DPKI_sim", "--", "exp", tuple(color[:3])),
        ]:
            x, y = finite_series(group, "lambda", column)
            if len(x) == 0:
                continue
            out[column] = smooth_monotone_xy(x, y, dense_x)
            ax.plot(
                dense_x,
                out[column],
                style,
                color=line_color,
                linewidth=1.6,
                label=f"{label_prefix} {label_suffix}",
            )
            if column == "DPKI_sim":
                ax.scatter(
                    x,
                    y,
                    marker="o",
                    facecolors="none",
                    edgecolors=color,
                    linewidths=1.1,
                    s=26,
                    zorder=3,
                )
        smooth_rows.append(out)

    ax.set_xlabel(r"$\lambda$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.set_xlim(float(frame["lambda"].min()), float(frame["lambda"].max()))
    if args.ylim:
        ax.set_ylim(*args.ylim)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=7, frameon=True, framealpha=1.0)
    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)

    smooth = pd.concat(smooth_rows, ignore_index=True) if smooth_rows else pd.DataFrame({"lambda": dense_x})
    write_lambda_figure_data(frame, smooth, output_dir)
    return smooth


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone real λ sweep for the DPKI/PKI experiment.")
    parser.add_argument("--lambda-values", type=parse_float_list, default=parse_float_list("2,3,4,5,6,7,8,9"))
    parser.add_argument("--mean-block-ms-values", type=parse_float_list, default=parse_float_list("80,60,50"))
    parser.add_argument("--requests", type=int, default=2000)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--p-manage", type=float, default=0.1)
    parser.add_argument("--gamma-on-chain", type=float, default=0.1)
    parser.add_argument("--q-manage", type=float, default=0.3)
    parser.add_argument("--service-cas", type=int, default=4)
    parser.add_argument("--service-shape-mode", default="none")
    parser.add_argument("--actual-execution-mode", default="serial", choices=["serial", "parallel"])
    parser.add_argument("--dpki-root-read-mode", default="chain", choices=["chain", "cache", "cached"])
    parser.add_argument("--dpki-proof-read-mode", default="http", choices=["http", "local", "cache", "cached"])
    parser.add_argument("--dpki-proof-base-port", type=int, default=20080)
    parser.add_argument("--dpki-q-mode", default="config", choices=["config", "queue"])
    parser.add_argument("--dpki-auth-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-management-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-auth-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-cross-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-management-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-proof-http-mean-ms", type=float, default=7.5)
    parser.add_argument("--dpki-proof-http-tail-probability", type=float, default=0.05)
    parser.add_argument("--dpki-proof-http-tail-multiplier", type=float, default=15.0)
    parser.add_argument("--dpki-auth-transfer-http-mean-ms", type=float, default=1.0)
    parser.add_argument("--dpki-auth-transfer-http-tail-probability", type=float, default=0.22)
    parser.add_argument("--dpki-auth-transfer-http-tail-multiplier", type=float, default=6.0)
    parser.add_argument("--dpki-management-http-mean-ms", type=float, default=10.0)
    parser.add_argument("--dpki-management-http-tail-probability", type=float, default=0.35)
    parser.add_argument("--dpki-management-http-tail-multiplier", type=float, default=10.0)
    parser.add_argument("--dpki-management-transfer-http-mean-ms", type=float, default=30.0)
    parser.add_argument("--dpki-management-transfer-http-tail-probability", type=float, default=0.35)
    parser.add_argument("--dpki-management-transfer-http-tail-multiplier", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=81001)
    parser.add_argument("--tag", default="result")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--restart-pow", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stop-pow", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--ylim", type=parse_float_list, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.ylim and len(args.ylim) != 2:
        raise SystemExit("--ylim must contain exactly two values, e.g. 0,0.5")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else SCRIPT_DIR / "result"
    output_dir.mkdir(parents=True, exist_ok=True)

    specs = make_specs(args)
    try:
        all_points: list[pd.DataFrame] = []
        all_kinds: list[pd.DataFrame] = []
        all_tx: list[pd.DataFrame] = []
        for mean_block_ms in args.mean_block_ms_values:
            if args.restart_pow:
                restart_pow(int(mean_block_ms))
            block_specs = [(x, spec) for x, spec in specs if f"_blockms_{fmt_value(mean_block_ms)}_" in spec.label]
            points, by_kind, tx_health = collect_sweep(block_specs, "lambda", args.reuse_existing)
            add_block_metadata(points, tx_health, block_specs, args)
            if not by_kind.empty:
                by_kind["meanBlockMs"] = float(mean_block_ms)
            all_points.append(points)
            all_kinds.append(by_kind)
            all_tx.append(tx_health)

        points = pd.concat(all_points, ignore_index=True).sort_values(["meanBlockMs", "lambda"])
        by_kind = pd.concat(all_kinds, ignore_index=True) if all_kinds else pd.DataFrame()
        tx_health = pd.concat(all_tx, ignore_index=True) if all_tx else pd.DataFrame()
        check = write_outputs(output_dir, "lambda_ET", "lambda", points, by_kind, tx_health, args)
        plot_lambda(points, output_dir, "lambda_ET", args)
        if output_dir == SCRIPT_DIR / "result":
            mirror_final_outputs(output_dir, SCRIPT_DIR)
        print(points[["meanBlockMs", "lambda", "DPKI_sim", "DPKI_lower_theory", "DPKI_upper_theory", "PKI_sim", "PKI_theory"]].to_string(index=False))
        print(check[["lambda", "DPKI_in_bounds", "DPKI_minus_lower", "DPKI_minus_upper", "PKI_abs_error"]].to_string(index=False))
        print(f"wrote Fig5 lambda outputs to {output_dir}")
    finally:
        if args.stop_pow:
            stop_pow()


if __name__ == "__main__":
    main()
