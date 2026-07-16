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
    for index, m_value in enumerate(args.m_values):
        label = f"{args.tag}_M_{fmt_value(m_value)}_lambda_{fmt_value(args.lambda_arrival)}_r{args.requests}"
        run_seed = args.seed if args.same_trace_across_m else (args.seed + index * 101)
        specs.append(
            (
                float(m_value),
                RunSpec(
                    label=label,
                    sweep="M_experiment",
                    x_name="M",
                    x_value=float(m_value),
                    epsilon_points=epsilon_text(args.epsilon),
                    requests=args.requests,
                    lambda_arrival=args.lambda_arrival,
                    p_manage=args.p_manage,
                    gamma_on_chain=args.gamma_on_chain,
                    q_manage=args.q_manage,
                    service_cas=int(m_value),
                    lambda_block=args.lambda_block,
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
                    pki_entity_pool_size=args.pki_entity_pool_size,
                    pki_management_pool_size=args.pki_management_pool_size,
                    pki_route_mode=args.pki_route_mode,
                    pki_subject_selection_mode=args.pki_subject_selection_mode,
                    dpki_q_mode=args.dpki_q_mode,
                    seed=run_seed,
                ),
            )
        )
    return specs


def apply_pointwise_theory(
    points: pd.DataFrame,
    pki_mu_scale: float = 1.0,
) -> pd.DataFrame:
    out = points.copy()
    for column in ["DPKI_upper_theory", "DPKI_lower_theory", "PKI_theory"]:
        if column in out:
            out[f"{column}_pointMeasured"] = out[column]

    upper_values: list[float] = []
    lower_values: list[float] = []
    pki_values: list[float] = []
    pki_rhos: list[float] = []
    for _, row in out.iterrows():
        lambda_total = float(row["lambdaTotalMeasured"])
        p_manage = float(row["pManageMeasured"])
        gamma_on_chain = float(row["gammaOnChainMeasured"])
        q_manage = float(row["qManageMeasured"])
        mu = float(row["muModelOffchainAuthMeasured"])
        lambda_block = float(row["lambdaBlockMeasured"])
        m_value = int(row["M"])
        epsilon = float(row["epsilon"])
        pki_mu = float(row["pkiMuPrimaryAuthMeasured"]) * float(pki_mu_scale)
        pki_q_manage = float(row["pkiQManageMeasured"])

        upper = theoretical_values_dpki_upper_bound(
            lambda_total,
            p_manage,
            q_manage,
            mu,
            m_value,
            gamma_on_chain,
            lambda_block,
            epsilon,
        )["E_T_total"]
        lower = theoretical_values_dpki_lower_bound(
            lambda_total,
            p_manage,
            q_manage,
            mu,
            m_value,
            gamma_on_chain,
            lambda_block,
            epsilon,
        )["E_T_total"]
        params = ModelParams(
            lambda_total=lambda_total,
            p_manage=p_manage,
            q_manage=q_manage,
            mu=mu,
            service_cas=m_value,
            gamma_on_chain=gamma_on_chain,
            lambda_block=lambda_block,
            pki_mu=pki_mu,
            pki_q_manage=pki_q_manage,
            pki_cross_extra_mu=pki_mu,
        )
        pki, rho = pki_theory_value(params, epsilon)
        upper_values.append(float(upper))
        lower_values.append(float(lower))
        pki_values.append(float(pki))
        pki_rhos.append(float(rho))

    out["DPKI_upper_theory"] = upper_values
    out["DPKI_lower_theory"] = lower_values
    out["PKI_theory"] = pki_values
    out["PKI_rho"] = pki_rhos
    out["calibrationScope"] = "M-pointwise-measured-parameters"
    out["MPoint_pki_mu_scale"] = float(pki_mu_scale)
    return out


def finite_series(frame: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    data = frame[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna().sort_values(x_col)
    return data[x_col].astype(float).to_numpy(), data[y_col].astype(float).to_numpy()


def step_curve_points(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0:
        return np.array([], dtype=float), np.array([], dtype=float)
    if len(x) == 1:
        return x.copy(), y.copy()

    midpoints = (x[:-1] + x[1:]) / 2.0
    step_x = [x[0]]
    step_y = [y[0]]
    for index, midpoint in enumerate(midpoints):
        step_x.extend([midpoint, midpoint])
        step_y.extend([y[index], y[index + 1]])
    step_x.append(x[-1])
    step_y.append(y[-1])
    return np.asarray(step_x, dtype=float), np.asarray(step_y, dtype=float)


def plot_m_sweep(points: pd.DataFrame, output_dir: Path, ylim: tuple[float, float] | None = None) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = points.sort_values("M").replace([np.inf, -np.inf], np.nan)
    base_x = frame["M"].astype(float).to_numpy()
    curve_x, _ = step_curve_points(base_x, base_x)
    smooth = pd.DataFrame({"M": curve_x})
    series = [
        ("DPKI_upper_theory", "DPKI Upper Bound", "-", (0.0, 0.5, 0.0), None),
        ("DPKI_lower_theory", "DPKI Lower Bound", "-", (0.0, 0.447, 0.741), None),
        ("DPKI_sim", "DPKI Experimental Trend", "--", (1.0, 0.4, 0.0), "o"),
        ("PKI_theory", "PKI Theory", "-", (0.85, 0.0, 0.0), None),
        ("PKI_sim", "PKI Experimental", "", (0.85, 0.0, 0.0), "D"),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, label, style, color, marker in series:
        x, y = finite_series(frame, "M", column)
        if len(x) == 0:
            continue
        step_x, step_y = step_curve_points(x, y)
        smooth[column] = step_y
        if style:
            ax.plot(step_x, step_y, style, color=color, linewidth=1.8, label=label)
        if marker:
            point_label = "DPKI Experimental" if column == "DPKI_sim" else label
            ax.scatter(
                x,
                y,
                marker=marker,
                facecolors="none",
                edgecolors=color,
                linewidths=1.2,
                s=28 if marker == "o" else 32,
                label=point_label,
                zorder=3,
            )
    ax.set_xlabel(r"$M$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.set_xlim(float(frame["M"].min()), float(frame["M"].max()))
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8, frameon=True, framealpha=1.0)
    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)
    for column in ["DPKI_upper_theory", "DPKI_lower_theory", "DPKI_sim", "PKI_theory", "PKI_sim"]:
        if column not in smooth.columns:
            smooth[column] = np.nan
    write_figure_data(frame, smooth, "M", output_dir)
    return smooth


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone real M sweep for the DPKI/PKI experiment.")
    parser.add_argument("--m-values", type=parse_float_list, default=parse_float_list("2,3,4,5,6,7,8,9"))
    parser.add_argument("--requests", type=int, default=10000)
    parser.add_argument("--lambda-arrival", type=float, default=28.0)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--p-manage", type=float, default=0.1)
    parser.add_argument("--gamma-on-chain", type=float, default=0.0)
    parser.add_argument("--q-manage", type=float, default=0.6)
    parser.add_argument("--lambda-block", type=float, default=30.0)
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
    parser.add_argument("--pki-entity-pool-size", type=int, default=64)
    parser.add_argument("--pki-management-pool-size", type=int, default=64)
    parser.add_argument("--pki-route-mode", default="balanced", choices=["hash", "balanced", "mod", "ordinal"])
    parser.add_argument(
        "--pki-subject-selection-mode",
        default="random",
        choices=["random", "cycle", "round-robin", "round_robin"],
    )
    parser.add_argument("--mean-block-ms", type=int, default=20)
    parser.add_argument("--seed", type=int, default=83001)
    parser.add_argument("--same-trace-across-m", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tag", default="result")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--restart-pow", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stop-pow", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--ylim", type=parse_float_list, default=None)
    parser.add_argument("--pki-mu-scale", type=float, default=1.12)
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
        points, by_kind, tx_health = collect_sweep(make_specs(args), "M", args.reuse_existing)
        points = apply_pointwise_theory(points, pki_mu_scale=args.pki_mu_scale)
        check = write_outputs(output_dir, "M_ET", "M", points, by_kind, tx_health, args)
        plot_m_sweep(points, output_dir, ylim=tuple(args.ylim) if args.ylim else None)
        if output_dir == SCRIPT_DIR / "result":
            mirror_final_outputs(output_dir, SCRIPT_DIR)
        print(points[["M", "DPKI_sim", "DPKI_lower_theory", "DPKI_upper_theory", "PKI_sim", "PKI_theory"]].to_string(index=False))
        print(check[["M", "DPKI_in_bounds", "DPKI_minus_lower", "DPKI_minus_upper", "PKI_abs_error"]].to_string(index=False))
        if not tx_health.empty:
            print(tx_health[["M", "txCount", "maxTxTotalMs", "slowTxOver1000ms"]].to_string(index=False))
        print(f"wrote Fig8 M outputs to {output_dir}")
    finally:
        if args.stop_pow:
            stop_pow()


if __name__ == "__main__":
    main()
