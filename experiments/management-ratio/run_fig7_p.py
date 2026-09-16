from __future__ import annotations

import argparse
import sys
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

from figure_dpki_pki_runtime.backend import (  # noqa: E402
    ModelParams,
    pki_theory_value,
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)
from figure_dpki_pki_runtime.sweep_common import (  # noqa: E402
    RunSpec,
    collect_sweep,
    fmt_value,
    mirror_final_outputs,
    parse_float_list,
    restart_pow,
    stop_pow,
    write_figure_data,
    write_outputs,
)


def epsilon_text(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def make_specs(args: argparse.Namespace) -> list[tuple[float, RunSpec]]:
    specs: list[tuple[float, RunSpec]] = []
    for index, p_value in enumerate(args.p_values):
        label = f"{args.tag}_p_{fmt_value(p_value)}_r{args.requests}"
        specs.append(
            (
                float(p_value),
                RunSpec(
                    label=label,
                    sweep="p_experiment",
                    x_name="p",
                    x_value=float(p_value),
                    epsilon_points=epsilon_text(args.epsilon),
                    requests=args.requests,
                    lambda_arrival=args.lambda_arrival,
                    p_manage=float(p_value),
                    gamma_on_chain=args.gamma_on_chain,
                    q_manage=args.q_manage,
                    service_cas=args.service_cas,
                    dpki_offchain_workers=args.dpki_offchain_workers,
                    max_onchain_in_flight=args.max_onchain_in_flight,
                    tx_senders=args.tx_senders,
                    lambda_block=args.lambda_block,
                    arrival_mode="wall",
                    kind_plan_mode="fixed",
                    dpki_root_read_mode=args.dpki_root_read_mode,
                    dpki_proof_read_mode=args.dpki_proof_read_mode,
                    dpki_proof_base_port=args.dpki_proof_base_port,
                    actual_execution_mode=args.actual_execution_mode,
                    seed=args.seed + index * 101,
                ),
            )
        )
    return specs








def finite_series(frame: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    data = frame[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna().sort_values(x_col)
    return data[x_col].astype(float).to_numpy(), data[y_col].astype(float).to_numpy()


def plot_p_sweep(points: pd.DataFrame, output_dir: Path, ylim=None) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = points.sort_values("p").replace([np.inf, -np.inf], np.nan)
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
            ax.plot(group["p"], group[column], linestyle=style, marker=marker,
                    markerfacecolor="none", label=label + suffix)
    ax.set_xlabel(r"$p$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)
    write_figure_data(frame, frame, "p", output_dir)
    return frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone real p sweep for the DPKI/PKI experiment.")
    parser.add_argument("--p-values", type=parse_float_list, default=parse_float_list("0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5"))
    parser.add_argument("--requests", type=int, default=2000)
    parser.add_argument("--lambda-arrival", type=float, default=4.0)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--gamma-on-chain", type=float, default=0.3)
    parser.add_argument("--q-manage", type=float, default=0.45)
    parser.add_argument("--service-cas", type=int, default=4)
    parser.add_argument("--dpki-offchain-workers", type=int, default=None)
    parser.add_argument("--max-onchain-in-flight", type=int, default=1)
    parser.add_argument("--tx-senders", type=int, default=1)
    parser.add_argument("--actual-execution-mode", default="parallel", choices=["serial", "parallel"])
    parser.add_argument("--dpki-root-read-mode", default="chain", choices=["chain", "cache", "cached"])
    parser.add_argument("--dpki-proof-read-mode", default="http", choices=["http", "local", "cache", "cached"])
    parser.add_argument("--dpki-proof-base-port", type=int, default=20080)
    parser.add_argument("--lambda-block", type=float, default=22.0)
    parser.add_argument("--mean-block-ms", type=int, default=28)
    parser.add_argument("--seed", type=int, default=82001)
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

    try:
        if args.restart_pow:
            restart_pow(args.mean_block_ms)
        points, by_kind, tx_health = collect_sweep(make_specs(args), "p", args.reuse_existing)
        check = write_outputs(output_dir, "p_ET", "p", points, by_kind, tx_health, args)
        plot_p_sweep(points, output_dir, ylim=tuple(args.ylim) if args.ylim else None)
        if output_dir == SCRIPT_DIR / "result":
            mirror_final_outputs(output_dir, SCRIPT_DIR)
        print(points[["p", "DPKI_sim", "DPKI_lower_theory", "DPKI_upper_theory", "PKI_sim", "PKI_theory"]].to_string(index=False))
        print(check[["p", "DPKI_in_bounds", "DPKI_minus_lower", "DPKI_minus_upper", "PKI_abs_error"]].to_string(index=False))
        if not tx_health.empty:
            print(tx_health[["p", "txCount", "maxTxTotalMs", "slowTxOver1000ms"]].to_string(index=False))
        print(f"wrote Fig7 p outputs to {output_dir}")
    finally:
        if args.stop_pow:
            stop_pow()


if __name__ == "__main__":
    main()
