from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
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
                    service_shape_mode=args.service_shape_mode,
                    arrival_mode="virtual",
                    kind_plan_mode="fixed",
                    dpki_root_read_mode=args.dpki_root_read_mode,
                    dpki_proof_read_mode=args.dpki_proof_read_mode,
                    dpki_proof_base_port=args.dpki_proof_base_port,
                    actual_execution_mode=args.actual_execution_mode,
                    dpki_auth_shape_mean_ms=args.dpki_auth_shape_mean_ms,
                    dpki_cross_shape_mean_ms=args.dpki_cross_shape_mean_ms,
                    dpki_onchain_shape_mean_ms=args.dpki_onchain_shape_mean_ms,
                    dpki_intra_offchain_shape_mean_ms=args.dpki_intra_offchain_shape_mean_ms,
                    dpki_management_shape_mean_ms=args.dpki_management_shape_mean_ms,
                    pki_auth_shape_mean_ms=args.pki_auth_shape_mean_ms,
                    pki_cross_shape_mean_ms=args.pki_cross_shape_mean_ms,
                    pki_intra_shape_mean_ms=args.pki_intra_shape_mean_ms,
                    pki_management_shape_mean_ms=args.pki_management_shape_mean_ms,
                    dpki_proof_http_mean_ms=args.dpki_proof_http_mean_ms,
                    dpki_proof_http_tail_probability=args.dpki_proof_http_tail_probability,
                    dpki_proof_http_tail_multiplier=args.dpki_proof_http_tail_multiplier,
                    dpki_auth_transfer_http_mean_ms=args.dpki_auth_transfer_http_mean_ms,
                    dpki_auth_transfer_http_tail_probability=args.dpki_auth_transfer_http_tail_probability,
                    dpki_auth_transfer_http_tail_multiplier=args.dpki_auth_transfer_http_tail_multiplier,
                    dpki_onchain_extra_http_mean_ms=args.dpki_onchain_extra_http_mean_ms,
                    dpki_onchain_extra_http_tail_probability=args.dpki_onchain_extra_http_tail_probability,
                    dpki_onchain_extra_http_tail_multiplier=args.dpki_onchain_extra_http_tail_multiplier,
                    dpki_cross_extra_http_mean_ms=args.dpki_cross_extra_http_mean_ms,
                    dpki_cross_extra_http_tail_probability=args.dpki_cross_extra_http_tail_probability,
                    dpki_cross_extra_http_tail_multiplier=args.dpki_cross_extra_http_tail_multiplier,
                    dpki_management_http_mean_ms=args.dpki_management_http_mean_ms,
                    dpki_management_http_tail_probability=args.dpki_management_http_tail_probability,
                    dpki_management_http_tail_multiplier=args.dpki_management_http_tail_multiplier,
                    dpki_management_transfer_http_mean_ms=args.dpki_management_transfer_http_mean_ms,
                    dpki_management_transfer_http_tail_probability=args.dpki_management_transfer_http_tail_probability,
                    dpki_management_transfer_http_tail_multiplier=args.dpki_management_transfer_http_tail_multiplier,
                    dpki_management_extra_http_mean_ms=args.dpki_management_extra_http_mean_ms,
                    dpki_management_extra_http_tail_probability=args.dpki_management_extra_http_tail_probability,
                    dpki_management_extra_http_tail_multiplier=args.dpki_management_extra_http_tail_multiplier,
                    pki_auth_http_mean_ms=args.pki_auth_http_mean_ms,
                    pki_auth_http_tail_probability=args.pki_auth_http_tail_probability,
                    pki_auth_http_tail_multiplier=args.pki_auth_http_tail_multiplier,
                    pki_auth_transfer_http_mean_ms=args.pki_auth_transfer_http_mean_ms,
                    pki_auth_transfer_http_tail_probability=args.pki_auth_transfer_http_tail_probability,
                    pki_auth_transfer_http_tail_multiplier=args.pki_auth_transfer_http_tail_multiplier,
                    pki_cross_extra_http_mean_ms=args.pki_cross_extra_http_mean_ms,
                    pki_cross_extra_http_tail_probability=args.pki_cross_extra_http_tail_probability,
                    pki_cross_extra_http_tail_multiplier=args.pki_cross_extra_http_tail_multiplier,
                    pki_management_http_mean_ms=args.pki_management_http_mean_ms,
                    pki_management_http_tail_probability=args.pki_management_http_tail_probability,
                    pki_management_http_tail_multiplier=args.pki_management_http_tail_multiplier,
                    pki_management_transfer_http_mean_ms=args.pki_management_transfer_http_mean_ms,
                    pki_management_transfer_http_tail_probability=args.pki_management_transfer_http_tail_probability,
                    pki_management_transfer_http_tail_multiplier=args.pki_management_transfer_http_tail_multiplier,
                    pki_management_extra_http_mean_ms=args.pki_management_extra_http_mean_ms,
                    pki_management_extra_http_tail_probability=args.pki_management_extra_http_tail_probability,
                    pki_management_extra_http_tail_multiplier=args.pki_management_extra_http_tail_multiplier,
                    seed=args.seed + index * 101,
                ),
            )
        )
    return specs


def apply_fixed_service_theory(
    points: pd.DataFrame,
    q_manage_override: float | None = None,
    pki_mu_scale: float = 0.95,
) -> pd.DataFrame:
    out = points.copy()
    for column in ["DPKI_upper_theory", "DPKI_lower_theory", "PKI_theory"]:
        if column in out:
            out[f"{column}_pointMeasured"] = out[column]

    def mean_col(column: str) -> float:
        return float(pd.to_numeric(out[column], errors="coerce").mean())

    fixed = {
        "lambda_total": mean_col("lambdaTotalMeasured"),
        "gamma_on_chain": mean_col("gammaOnChainMeasured"),
        "q_manage": float(q_manage_override if q_manage_override is not None else mean_col("qManageMeasured")),
        "mu": mean_col("muModelOffchainAuthMeasured"),
        "lambda_block": mean_col("lambdaBlockMeasured"),
        "service_cas": int(round(mean_col("serviceCAs"))),
        "pki_mu": mean_col("pkiMuPrimaryAuthMeasured") * float(pki_mu_scale),
        "pki_q_manage": mean_col("pkiQManageMeasured"),
    }

    upper_values: list[float] = []
    lower_values: list[float] = []
    pki_values: list[float] = []
    pki_rhos: list[float] = []
    for _, row in out.iterrows():
        epsilon = float(row["epsilon"])
        p_manage = float(row["p"])
        upper = theoretical_values_dpki_upper_bound(
            fixed["lambda_total"],
            p_manage,
            fixed["q_manage"],
            fixed["mu"],
            fixed["service_cas"],
            fixed["gamma_on_chain"],
            fixed["lambda_block"],
            epsilon,
        )
        lower = theoretical_values_dpki_lower_bound(
            fixed["lambda_total"],
            p_manage,
            fixed["q_manage"],
            fixed["mu"],
            fixed["service_cas"],
            fixed["gamma_on_chain"],
            fixed["lambda_block"],
            epsilon,
        )
        params = ModelParams(
            lambda_total=fixed["lambda_total"],
            p_manage=p_manage,
            q_manage=fixed["q_manage"],
            mu=fixed["mu"],
            service_cas=fixed["service_cas"],
            gamma_on_chain=fixed["gamma_on_chain"],
            lambda_block=fixed["lambda_block"],
            pki_mu=fixed["pki_mu"],
            pki_q_manage=fixed["pki_q_manage"],
            pki_cross_extra_mu=fixed["pki_mu"],
        )
        pki_theory, pki_rho = pki_theory_value(params, epsilon)
        upper_values.append(float(upper["E_T_total"]))
        lower_values.append(float(lower["E_T_total"]))
        pki_values.append(float(pki_theory))
        pki_rhos.append(float(pki_rho))

    out["DPKI_upper_theory"] = upper_values
    out["DPKI_lower_theory"] = lower_values
    out["PKI_theory"] = pki_values
    out["PKI_rho"] = pki_rhos
    out["calibrationScope"] = "p-fixed-service-parameters"
    for key, value in fixed.items():
        out[f"PFixed_{key}"] = value
    out["PFixed_pki_mu_scale"] = float(pki_mu_scale)
    return out


def pava_increasing(y: np.ndarray) -> np.ndarray:
    blocks: list[tuple[float, int]] = []
    for value in y.astype(float):
        blocks.append((float(value), 1))
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            v1, n1 = blocks.pop()
            v0, n0 = blocks.pop()
            blocks.append(((v0 * n0 + v1 * n1) / (n0 + n1), n0 + n1))
    return np.array([value for value, count in blocks for _ in range(count)], dtype=float)


def smooth_monotone(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray) -> np.ndarray:
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    order = np.argsort(x)
    x_sorted = x[order].astype(float)
    y_sorted = pava_increasing(y[order].astype(float))
    return PchipInterpolator(x_sorted, y_sorted, extrapolate=False)(dense_x)


def finite_series(frame: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    data = frame[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna().sort_values(x_col)
    return data[x_col].astype(float).to_numpy(), data[y_col].astype(float).to_numpy()


def plot_p_sweep(points: pd.DataFrame, output_dir: Path, ylim: tuple[float, float] | None = None) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = points.sort_values("p").replace([np.inf, -np.inf], np.nan)
    dense_x = np.linspace(float(frame["p"].min()), float(frame["p"].max()), 260)
    smooth = pd.DataFrame({"p": dense_x})
    series = [
        ("DPKI_upper_theory", "DPKI Upper Bound", "-", (0.0, 0.5, 0.0), None),
        ("DPKI_lower_theory", "DPKI Lower Bound", "-", (0.0, 0.447, 0.741), None),
        ("DPKI_sim", "DPKI Experimental Trend", "--", (1.0, 0.4, 0.0), "o"),
        ("PKI_theory", "PKI Theory", "-", (0.85, 0.0, 0.0), None),
        ("PKI_sim", "PKI Experimental", "", (0.85, 0.0, 0.0), "D"),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, label, style, color, marker in series:
        x, y = finite_series(frame, "p", column)
        if len(x) == 0:
            continue
        smooth[column] = smooth_monotone(x, y, dense_x)
        if style:
            ax.plot(dense_x, smooth[column], style, color=color, linewidth=1.8, label=label)
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
    ax.set_xlabel(r"$p$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.set_xlim(float(frame["p"].min()), float(frame["p"].max()))
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
    write_figure_data(frame, smooth, "p", output_dir)
    return smooth


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
    parser.add_argument("--service-shape-mode", default="none")
    parser.add_argument("--actual-execution-mode", default="serial", choices=["serial", "parallel"])
    parser.add_argument("--dpki-root-read-mode", default="chain", choices=["chain", "cache", "cached"])
    parser.add_argument("--dpki-proof-read-mode", default="http", choices=["http", "local", "cache", "cached"])
    parser.add_argument("--dpki-proof-base-port", type=int, default=20080)
    parser.add_argument("--dpki-auth-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-cross-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-onchain-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-intra-offchain-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-management-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-auth-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-cross-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-intra-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-management-shape-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-proof-http-mean-ms", type=float, default=7.5)
    parser.add_argument("--dpki-proof-http-tail-probability", type=float, default=0.05)
    parser.add_argument("--dpki-proof-http-tail-multiplier", type=float, default=15.0)
    parser.add_argument("--dpki-auth-transfer-http-mean-ms", type=float, default=1.0)
    parser.add_argument("--dpki-auth-transfer-http-tail-probability", type=float, default=0.22)
    parser.add_argument("--dpki-auth-transfer-http-tail-multiplier", type=float, default=6.0)
    parser.add_argument("--dpki-onchain-extra-http-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-onchain-extra-http-tail-probability", type=float, default=0.0)
    parser.add_argument("--dpki-onchain-extra-http-tail-multiplier", type=float, default=1.0)
    parser.add_argument("--dpki-cross-extra-http-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-cross-extra-http-tail-probability", type=float, default=0.0)
    parser.add_argument("--dpki-cross-extra-http-tail-multiplier", type=float, default=1.0)
    parser.add_argument("--dpki-management-http-mean-ms", type=float, default=10.0)
    parser.add_argument("--dpki-management-http-tail-probability", type=float, default=0.35)
    parser.add_argument("--dpki-management-http-tail-multiplier", type=float, default=10.0)
    parser.add_argument("--dpki-management-transfer-http-mean-ms", type=float, default=30.0)
    parser.add_argument("--dpki-management-transfer-http-tail-probability", type=float, default=0.35)
    parser.add_argument("--dpki-management-transfer-http-tail-multiplier", type=float, default=10.0)
    parser.add_argument("--dpki-management-extra-http-mean-ms", type=float, default=0.0)
    parser.add_argument("--dpki-management-extra-http-tail-probability", type=float, default=0.0)
    parser.add_argument("--dpki-management-extra-http-tail-multiplier", type=float, default=1.0)
    parser.add_argument("--pki-auth-http-mean-ms", type=float, default=5.0)
    parser.add_argument("--pki-auth-http-tail-probability", type=float, default=0.20)
    parser.add_argument("--pki-auth-http-tail-multiplier", type=float, default=4.0)
    parser.add_argument("--pki-auth-transfer-http-mean-ms", type=float, default=8.0)
    parser.add_argument("--pki-auth-transfer-http-tail-probability", type=float, default=0.35)
    parser.add_argument("--pki-auth-transfer-http-tail-multiplier", type=float, default=7.0)
    parser.add_argument("--pki-cross-extra-http-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-cross-extra-http-tail-probability", type=float, default=0.0)
    parser.add_argument("--pki-cross-extra-http-tail-multiplier", type=float, default=1.0)
    parser.add_argument("--pki-management-http-mean-ms", type=float, default=6.0)
    parser.add_argument("--pki-management-http-tail-probability", type=float, default=0.15)
    parser.add_argument("--pki-management-http-tail-multiplier", type=float, default=3.0)
    parser.add_argument("--pki-management-transfer-http-mean-ms", type=float, default=8.0)
    parser.add_argument("--pki-management-transfer-http-tail-probability", type=float, default=0.20)
    parser.add_argument("--pki-management-transfer-http-tail-multiplier", type=float, default=4.0)
    parser.add_argument("--pki-management-extra-http-mean-ms", type=float, default=0.0)
    parser.add_argument("--pki-management-extra-http-tail-probability", type=float, default=0.0)
    parser.add_argument("--pki-management-extra-http-tail-multiplier", type=float, default=1.0)
    parser.add_argument("--lambda-block", type=float, default=22.0)
    parser.add_argument("--mean-block-ms", type=int, default=28)
    parser.add_argument("--seed", type=int, default=82001)
    parser.add_argument("--tag", default="result")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--restart-pow", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stop-pow", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--ylim", type=parse_float_list, default=None)
    parser.add_argument("--pki-mu-scale", type=float, default=1.0)
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
        points = apply_fixed_service_theory(
            points,
            q_manage_override=args.q_manage,
            pki_mu_scale=args.pki_mu_scale,
        )
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
