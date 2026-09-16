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

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from figure_dpki_pki_runtime.backend import RunSpec  # noqa: E402
from figure_dpki_pki_runtime.sweep_common import (  # noqa: E402
    SWEEP_ROOT,
    collect_sweep,
    fmt_value,
    mirror_final_outputs,
    parse_float_list,
    restart_pow,
    stop_pow,
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
                        arrival_mode="wall",
                        kind_plan_mode="fixed",
                        dpki_root_read_mode=args.dpki_root_read_mode,
                        dpki_proof_read_mode=args.dpki_proof_read_mode,
                        dpki_proof_base_port=args.dpki_proof_base_port,
                        actual_execution_mode=args.actual_execution_mode,
                        skip_pki=True,
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








def finite_series(frame: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    series = frame[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna().sort_values(x_col)
    return series[x_col].astype(float).to_numpy(), series[y_col].astype(float).to_numpy()


def lighter(color: tuple[float, ...], amount: float = 0.55) -> tuple[float, float, float]:
    return tuple(float(component + (1.0 - component) * amount) for component in color[:3])


def write_lambda_figure_data(points: pd.DataFrame, plotted: pd.DataFrame, output_dir: Path) -> None:
    raw = points.rename(columns={"DPKI_upper_theory": "DPKI_upper_bound", "DPKI_lower_theory": "DPKI_lower_bound", "DPKI_sim": "DPKI_experimental"}).copy()
    raw.insert(0, "dataKind", "measured_point")
    raw.to_csv(output_dir / "figure_data.csv", index=False)


def plot_lambda(points: pd.DataFrame, output_dir: Path, prefix: str, args: argparse.Namespace) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = points.sort_values("lambda").replace([np.inf, -np.inf], np.nan)
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    groups = frame.groupby("meanBlockMs") if "meanBlockMs" in frame else [(None, frame)]
    for block_ms, group in groups:
        for column, label, style, marker in [
            ("DPKI_upper_theory", "DPKI Upper Bound", "-", ""),
            ("DPKI_lower_theory", "DPKI Lower Bound", "-", ""),
            ("DPKI_sim", "DPKI Experimental", "--", "o"),
            ("PKI_theory", "PKI Theory", "-", ""),
            ("PKI_sim", "PKI Experimental", "none", "D"),
        ]:
            if column not in group or group[column].isna().all():
                continue
            suffix = f" (block {block_ms:g} ms)" if block_ms is not None else ""
            ax.plot(group["lambda"], group[column], linestyle=style, marker=marker,
                    markerfacecolor="none", label=label + suffix)
    ax.set_xlabel(r"$\lambda$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)
    write_lambda_figure_data(frame, frame, output_dir)
    return frame


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
    parser.add_argument("--actual-execution-mode", default="parallel", choices=["serial", "parallel"])
    parser.add_argument("--dpki-root-read-mode", default="chain", choices=["chain", "cache", "cached"])
    parser.add_argument("--dpki-proof-read-mode", default="http", choices=["http", "local", "cache", "cached"])
    parser.add_argument("--dpki-proof-base-port", type=int, default=20080)
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
