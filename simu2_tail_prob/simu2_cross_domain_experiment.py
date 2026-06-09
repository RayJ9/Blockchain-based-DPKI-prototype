from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from simu3_compare_cross import (  # noqa: E402
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)


PKI_CROSS_DOMAIN_CHAIN_STEPS = 3


@dataclass(frozen=True)
class ModelParams:
    lambda_total: float = 4.5
    p_manage: float = 0.1
    q_manage: float = 0.3
    mu: float = 8.5
    service_cas: int = 6
    gamma_on_chain: float = 0.425
    lambda_block: float = 200.0


@dataclass(frozen=True)
class SimulationParams:
    sim_time: float = 100_000.0
    warmup_time: float = 10_000.0
    replications: int = 5
    seed: int = 3302


def exp_sample(rng: np.random.Generator, rate: float) -> float:
    if rate <= 0:
        return math.inf
    return float(rng.exponential(1.0 / rate))


def mean_dict(dicts: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted({key for row in dicts for key in row})
    averaged: dict[str, float] = {}
    for key in keys:
        values = np.array([row.get(key, np.nan) for row in dicts], dtype=float)
        averaged[key] = float(np.nanmean(values))
    return averaged


def run_dpki_experiment(
    params: ModelParams,
    sim: SimulationParams,
    epsilon: float,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Model-faithful DPKI experiment.

    Arrival classification follows the paper exactly:
    lambda_a = (1-p)(1-gamma)(1-epsilon)lambda
    lambda_b = [p + (1-p)epsilon + (1-p)(1-epsilon)gamma]lambda

    The on-chain path uses exhaustive Poisson batching. When a block enters
    execution, its packed requests are served serially with exponential service
    times, so E[T] is measured at transaction level and the second stage keeps
    the paper's Poisson/exponential service assumption.
    """

    rng = rng
    next_arrival = exp_sample(rng, params.lambda_total)
    next_block = math.inf
    mempool: list[tuple[float, float, bool, bool]] = []
    server_available = [0.0 for _ in range(params.service_cas)]
    executor_available = 0.0

    total_sum = 0.0
    total_count = 0
    offchain_sum = 0.0
    offchain_count = 0
    pool_wait_sum = 0.0
    pool_wait_count = 0
    execution_sum = 0.0
    execution_count = 0
    execution_queue_sum = 0.0
    execution_service_sum = 0.0

    total_arrivals = 0
    measured_arrivals = 0
    offchain_arrivals = 0
    onchain_arrivals = 0
    management_arrivals = 0
    cross_domain_arrivals = 0
    intra_onchain_arrivals = 0
    blocks = 0
    measured_blocks = 0

    def record_offchain(arrival_time: float) -> None:
        nonlocal total_sum, total_count, offchain_sum, offchain_count

        server_idx = min(range(params.service_cas), key=server_available.__getitem__)
        start_time = max(arrival_time, server_available[server_idx])
        finish_time = start_time + exp_sample(rng, params.mu)
        server_available[server_idx] = finish_time

        if arrival_time >= sim.warmup_time:
            latency = finish_time - arrival_time
            offchain_sum += latency
            offchain_count += 1
            total_sum += latency
            total_count += 1

    def record_block(block_time: float) -> None:
        nonlocal next_block, executor_available, total_sum, total_count
        nonlocal pool_wait_sum, pool_wait_count, execution_sum, execution_count
        nonlocal execution_queue_sum, execution_service_sum
        nonlocal blocks, measured_blocks

        batch = mempool.copy()
        mempool.clear()
        next_block = math.inf
        if not batch:
            return

        blocks += 1
        execution_service = sum(exp_sample(rng, 1.0 / service_mean) for _, service_mean, _, _ in batch)
        execution_start = max(block_time, executor_available)
        finish_time = execution_start + execution_service
        executor_available = finish_time

        measured_batch = [tx for tx in batch if tx[2]]
        if not measured_batch:
            return

        measured_blocks += 1
        n = len(measured_batch)
        sum_arrivals = sum(tx[0] for tx in measured_batch)

        pool_wait_sum += n * block_time - sum_arrivals
        pool_wait_count += n

        execution_delay = finish_time - block_time
        execution_queue = execution_start - block_time
        execution_sum += n * execution_delay
        execution_queue_sum += n * execution_queue
        execution_service_sum += n * execution_service
        execution_count += n

        total_sum += n * finish_time - sum_arrivals
        total_count += n

    while next_arrival <= sim.sim_time or mempool:
        if next_arrival <= sim.sim_time and next_arrival <= next_block:
            now = next_arrival
            total_arrivals += 1
            measured = now >= sim.warmup_time
            if measured:
                measured_arrivals += 1

            if rng.random() < params.p_manage:
                management_arrivals += 1
                onchain_arrivals += 1
                service_mean = 1.0 / (params.q_manage * params.mu)
                was_empty = not mempool
                mempool.append((now, service_mean, measured, True))
                if was_empty:
                    next_block = now + exp_sample(rng, params.lambda_block)
            else:
                if rng.random() < epsilon:
                    cross_domain_arrivals += 1
                    onchain_arrivals += 1
                    service_mean = 1.0 / params.mu
                    was_empty = not mempool
                    mempool.append((now, service_mean, measured, False))
                    if was_empty:
                        next_block = now + exp_sample(rng, params.lambda_block)
                elif rng.random() < params.gamma_on_chain:
                    intra_onchain_arrivals += 1
                    onchain_arrivals += 1
                    service_mean = 1.0 / params.mu
                    was_empty = not mempool
                    mempool.append((now, service_mean, measured, False))
                    if was_empty:
                        next_block = now + exp_sample(rng, params.lambda_block)
                else:
                    offchain_arrivals += 1
                    record_offchain(now)

            next_arrival = now + exp_sample(rng, params.lambda_total)
        else:
            record_block(next_block)

    lambda_a_target = (
        (1.0 - params.p_manage)
        * (1.0 - params.gamma_on_chain)
        * (1.0 - epsilon)
        * params.lambda_total
    )
    lambda_b_target = (
        params.p_manage
        + (1.0 - params.p_manage) * epsilon
        + (1.0 - params.p_manage) * (1.0 - epsilon) * params.gamma_on_chain
    ) * params.lambda_total

    return {
        "DPKI_sim": total_sum / total_count if total_count else math.nan,
        "E_T_offchain_sim": offchain_sum / offchain_count if offchain_count else math.nan,
        "E_T_pool_wait_sim": pool_wait_sum / pool_wait_count if pool_wait_count else math.nan,
        "E_T_execution_sim": execution_sum / execution_count if execution_count else math.nan,
        "E_T_execution_queue_sim": execution_queue_sum / execution_count if execution_count else math.nan,
        "E_T_execution_service_sim": execution_service_sum / execution_count if execution_count else math.nan,
        "measured_requests": float(total_count),
        "measured_arrivals": float(measured_arrivals),
        "total_arrivals": float(total_arrivals),
        "blocks": float(blocks),
        "measured_blocks": float(measured_blocks),
        "actual_offchain_ratio": offchain_arrivals / total_arrivals if total_arrivals else math.nan,
        "actual_onchain_ratio": onchain_arrivals / total_arrivals if total_arrivals else math.nan,
        "actual_management_ratio": management_arrivals / total_arrivals if total_arrivals else math.nan,
        "actual_cross_domain_ratio": cross_domain_arrivals / total_arrivals if total_arrivals else math.nan,
        "actual_intra_onchain_ratio": intra_onchain_arrivals / total_arrivals if total_arrivals else math.nan,
        "target_lambda_a": lambda_a_target,
        "target_lambda_b": lambda_b_target,
        "observed_lambda_a": offchain_arrivals / sim.sim_time,
        "observed_lambda_b": onchain_arrivals / sim.sim_time,
    }


def pki_theory_value(params: ModelParams, epsilon: float) -> tuple[float, float]:
    """Typical PKI benchmark from the paper's Eq. (49).

    Each service CA owns an isolated certificate domain. Cross-domain
    authentication verifies the trust chain Ea -> Sa -> Ga -> Gb, adding
    three sequential certificate-verification steps.
    """

    lambda_per_ca = params.lambda_total / params.service_cas
    p = params.p_manage
    q = params.q_manage
    mu = params.mu
    denominator = 1.0 - (p * lambda_per_ca / (q * mu)) - ((1.0 - p) * lambda_per_ca / mu)
    rho = (lambda_per_ca / mu) * (p / q + (1.0 - p))
    if denominator <= 0.0 or rho >= 1.0:
        return math.inf, rho

    waiting = (
        (lambda_per_ca / (q * q * mu * mu))
        * (p + (1.0 - p) * q * q)
        / denominator
    )
    service = p / (q * mu) + (1.0 + PKI_CROSS_DOMAIN_CHAIN_STEPS * epsilon) * (1.0 - p) / mu
    return waiting + service, rho


def run_pki_experiment(
    params: ModelParams,
    sim: SimulationParams,
    epsilon: float,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Simulate the paper's typical PKI cross-domain verification process.

    Requests are statically routed to the uniquely responsible service CA.
    A normal authentication verifies one certificate. A cross-domain
    authentication additionally verifies the three-hop trust chain
    Ea -> Sa -> Ga -> Gb, implemented as three serial exponential
    certificate-verification delays.
    """

    total_sum = 0.0
    total_count = 0
    management_count = 0
    auth_count = 0
    cross_count = 0
    chain_step_count = 0
    primary_queue_sum = 0.0
    primary_service_sum = 0.0
    chain_verify_sum = 0.0
    lambda_per_ca = params.lambda_total / params.service_cas

    for _ in range(params.service_cas):
        now = exp_sample(rng, lambda_per_ca)
        server_available = 0.0
        while now <= sim.sim_time:
            is_management = rng.random() < params.p_manage
            if is_management:
                management_count += 1
                service_rate = params.q_manage * params.mu
                chain_steps = 0
            else:
                auth_count += 1
                service_rate = params.mu
                is_cross_domain = rng.random() < epsilon
                chain_steps = PKI_CROSS_DOMAIN_CHAIN_STEPS if is_cross_domain else 0
                if is_cross_domain:
                    cross_count += 1
                    chain_step_count += chain_steps

            start_time = max(now, server_available)
            primary_service = exp_sample(rng, service_rate)
            finish_primary = start_time + primary_service
            server_available = finish_primary
            chain_verify = sum(exp_sample(rng, params.mu) for _ in range(chain_steps))
            finish_time = finish_primary + chain_verify

            if now >= sim.warmup_time:
                total_sum += finish_time - now
                total_count += 1
                primary_queue_sum += start_time - now
                primary_service_sum += primary_service
                chain_verify_sum += chain_verify

            now += exp_sample(rng, lambda_per_ca)

    total_arrivals = management_count + auth_count
    return {
        "PKI_sim": total_sum / total_count if total_count else math.nan,
        "PKI_measured_requests": float(total_count),
        "PKI_actual_management_ratio": management_count / total_arrivals if total_arrivals else math.nan,
        "PKI_actual_cross_domain_ratio": cross_count / auth_count if auth_count else math.nan,
        "PKI_chain_steps_per_request": chain_step_count / total_arrivals if total_arrivals else math.nan,
        "PKI_primary_queue_sim": primary_queue_sum / total_count if total_count else math.nan,
        "PKI_primary_service_sim": primary_service_sum / total_count if total_count else math.nan,
        "PKI_chain_verify_sim": chain_verify_sum / total_count if total_count else math.nan,
    }


def theory_rows(params: ModelParams, epsilon_values: Iterable[float]) -> pd.DataFrame:
    rows = []
    for epsilon in epsilon_values:
        upper = theoretical_values_dpki_upper_bound(
            params.lambda_total,
            params.p_manage,
            params.q_manage,
            params.mu,
            params.service_cas,
            params.gamma_on_chain,
            params.lambda_block,
            float(epsilon),
        )
        lower = theoretical_values_dpki_lower_bound(
            params.lambda_total,
            params.p_manage,
            params.q_manage,
            params.mu,
            params.service_cas,
            params.gamma_on_chain,
            params.lambda_block,
            float(epsilon),
        )
        pki_theory, pki_rho = pki_theory_value(params, float(epsilon))
        rows.append(
            {
                "epsilon": float(epsilon),
                "DPKI_upper_theory": upper["E_T_total"],
                "DPKI_lower_theory": lower["E_T_total"],
                "PKI_theory": pki_theory,
                "PKI_rho": pki_rho,
            }
        )
    return pd.DataFrame(rows)


def simulation_rows(
    params: ModelParams,
    sim: SimulationParams,
    epsilon_values: Iterable[float],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    detail_rows = []

    for eps_index, epsilon in enumerate(epsilon_values):
        dpki_reps = []
        pki_reps = []
        for rep in range(sim.replications):
            seed_base = sim.seed + eps_index * 10_000 + rep * 101
            dpki_rng = np.random.default_rng(seed_base)
            pki_rng = np.random.default_rng(seed_base + 53)
            dpki_reps.append(run_dpki_experiment(params, sim, float(epsilon), dpki_rng))
            pki_reps.append(run_pki_experiment(params, sim, float(epsilon), pki_rng))

        dpki_avg = mean_dict(dpki_reps)
        pki_avg = mean_dict(pki_reps)
        row = {
            "epsilon": float(epsilon),
            "DPKI_sim": dpki_avg["DPKI_sim"],
            "PKI_sim": pki_avg["PKI_sim"],
        }
        summary_rows.append(row)
        detail_rows.append({"epsilon": float(epsilon), **dpki_avg, **pki_avg})

        print(
            "epsilon={:.2f} DPKI_sim={:.6f} PKI_sim={:.6f} "
            "lambda_a={:.4f}/{:.4f} lambda_b={:.4f}/{:.4f} pki_cross={:.4f}".format(
                float(epsilon),
                row["DPKI_sim"],
                row["PKI_sim"],
                dpki_avg["observed_lambda_a"],
                dpki_avg["target_lambda_a"],
                dpki_avg["observed_lambda_b"],
                dpki_avg["target_lambda_b"],
                pki_avg["PKI_actual_cross_domain_ratio"],
            )
        )

    return pd.DataFrame(summary_rows), pd.DataFrame(detail_rows)


def save_combined(theory_df: pd.DataFrame, sim_df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    combined = pd.merge(theory_df, sim_df, on="epsilon", how="outer").sort_values("epsilon")
    combined.to_csv(out_dir / "combined_results_by_epsilon.csv", index=False)
    return combined


def save_lambda_summary(detail_df: pd.DataFrame, out_dir: Path) -> None:
    lambda_columns = {
        "epsilon": "epsilon",
        "target_lambda_a": "targetLambdaOffchain",
        "observed_lambda_a": "observedLambdaOffchain",
        "target_lambda_b": "targetLambdaOnchain",
        "observed_lambda_b": "observedLambdaOnchain",
        "actual_offchain_ratio": "actualOffChainRatio",
        "actual_onchain_ratio": "actualOnChainRatio",
        "actual_cross_domain_ratio": "actualCrossDomainRatio",
        "measured_requests": "measuredRequests",
        "total_arrivals": "totalArrivals",
        "blocks": "blocks",
        "measured_blocks": "measuredBlocks",
        "PKI_actual_cross_domain_ratio": "PKICrossDomainRatio",
        "PKI_chain_steps_per_request": "PKIChainStepsPerRequest",
    }
    detail_df[list(lambda_columns)].rename(columns=lambda_columns).to_csv(
        out_dir / "lambda_summary_by_epsilon.csv", index=False
    )


def save_bounds_check(params: ModelParams, sim_df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    exact_theory = theory_rows(params, sim_df["epsilon"].to_numpy())
    check = pd.merge(exact_theory, sim_df, on="epsilon", how="inner").sort_values("epsilon")
    check["DPKI_inside_bounds"] = (
        (check["DPKI_sim"] >= check["DPKI_lower_theory"])
        & (check["DPKI_sim"] <= check["DPKI_upper_theory"])
    )
    check["PKI_abs_error"] = (check["PKI_sim"] - check["PKI_theory"]).abs()
    check["DPKI_minus_PKI"] = check["DPKI_sim"] - check["PKI_sim"]
    check = check[
        [
            "epsilon",
            "DPKI_lower_theory",
            "DPKI_sim",
            "DPKI_upper_theory",
            "DPKI_inside_bounds",
            "PKI_theory",
            "PKI_sim",
            "PKI_abs_error",
            "DPKI_minus_PKI",
        ]
    ]
    check.to_csv(out_dir / "final_bounds_check.csv", index=False)
    return check


def plot_results(theory_df: pd.DataFrame, sim_df: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.3, 4.2))

    ax.plot(
        theory_df["epsilon"],
        theory_df["DPKI_upper_theory"],
        "--",
        color=(0.0, 0.5, 0.0),
        linewidth=1.5,
        label="DPKI Upper Bound",
    )
    ax.plot(
        theory_df["epsilon"],
        theory_df["DPKI_lower_theory"],
        "--",
        color=(0.0, 0.447, 0.741),
        linewidth=1.5,
        label="DPKI Lower Bound",
    )
    valid_dpki = sim_df.dropna(subset=["DPKI_sim"])
    ax.plot(
        valid_dpki["epsilon"],
        valid_dpki["DPKI_sim"],
        "-o",
        color=(1.0, 0.4, 0.0),
        linewidth=1.5,
        markersize=4,
        label="DPKI Experimental",
    )
    if "PKI_theory" in theory_df.columns:
        ax.plot(
            theory_df["epsilon"],
            theory_df["PKI_theory"],
            "-",
            color=(0.85, 0.0, 0.0),
            linewidth=1.2,
            alpha=0.75,
            label="_nolegend_",
        )
    if "PKI_sim" in sim_df.columns:
        valid_pki = sim_df.dropna(subset=["PKI_sim"])
        ax.plot(
            valid_pki["epsilon"],
            valid_pki["PKI_sim"],
            "-o",
            color=(0.85, 0.0, 0.0),
            linewidth=1.5,
            markersize=4,
            label="PKI Analytical/Experimental",
        )

    ax.set_xlabel(r"$\epsilon$")
    ax.set_ylabel(r"$E[T]$")
    xmin = float(min(theory_df["epsilon"].min(), sim_df["epsilon"].min()))
    xmax = float(max(theory_df["epsilon"].max(), sim_df["epsilon"].max()))
    tick_step = 0.05 if xmax <= 0.35 else 0.1
    ax.set_xlim(xmin, xmax)
    ax.set_xticks(np.arange(xmin, xmax + tick_step / 2, tick_step))
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend(loc="upper left", fontsize=8, frameon=True)
    fig.tight_layout()

    for stem in ("Fig7_epsilon_ET", "Fig3_epsilon_ET"):
        fig.savefig(out_dir / f"{stem}.png", dpi=300)
        fig.savefig(out_dir / f"{stem}.eps", format="eps")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate simu2 with cross-domain ratio epsilon on the x-axis."
    )
    parser.add_argument("--out-dir", type=Path, default=SCRIPT_DIR)
    parser.add_argument("--seed", type=int, default=3302)
    parser.add_argument("--sim-time", type=float, default=100_000.0)
    parser.add_argument("--warmup-time", type=float, default=10_000.0)
    parser.add_argument("--replications", type=int, default=5)
    parser.add_argument("--lambda-total", type=float, default=4.5)
    parser.add_argument("--p-manage", type=float, default=0.1)
    parser.add_argument("--q-manage", type=float, default=0.3)
    parser.add_argument("--mu", type=float, default=8.5)
    parser.add_argument("--service-cas", type=int, default=6)
    parser.add_argument("--gamma-on-chain", type=float, default=0.425)
    parser.add_argument("--lambda-block", type=float, default=200.0)
    parser.add_argument(
        "--epsilon-points",
        type=str,
        default="0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5",
        help="Comma-separated experimental epsilon points.",
    )
    parser.add_argument("--theory-points", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    params = ModelParams(
        lambda_total=args.lambda_total,
        p_manage=args.p_manage,
        q_manage=args.q_manage,
        mu=args.mu,
        service_cas=args.service_cas,
        gamma_on_chain=args.gamma_on_chain,
        lambda_block=args.lambda_block,
    )
    sim = SimulationParams(
        sim_time=args.sim_time,
        warmup_time=args.warmup_time,
        replications=args.replications,
        seed=args.seed,
    )

    epsilon_sim = np.array([float(value.strip()) for value in args.epsilon_points.split(",")])
    epsilon_theory = np.linspace(float(epsilon_sim.min()), float(epsilon_sim.max()), args.theory_points)

    print("simu2 epsilon experiment")
    print(f"params={params}")
    print(f"simulation={sim}")
    print("stage1 block generation: Poisson(lambda_block)")
    print("stage2 execution: exponential per-request service inside each packed block")

    theory_df = theory_rows(params, epsilon_theory)
    sim_df, detail_df = simulation_rows(params, sim, epsilon_sim)

    theory_df.to_csv(out_dir / "theory_results_by_epsilon.csv", index=False)
    sim_df.to_csv(out_dir / "simulation_results_by_epsilon.csv", index=False)
    detail_df.to_csv(out_dir / "simulation_results_by_epsilon_detailed.csv", index=False)
    save_combined(theory_df, sim_df, out_dir)
    save_lambda_summary(detail_df, out_dir)
    save_bounds_check(params, sim_df, out_dir)
    plot_results(theory_df, sim_df, out_dir)

    print(f"wrote {out_dir / 'theory_results_by_epsilon.csv'}")
    print(f"wrote {out_dir / 'simulation_results_by_epsilon.csv'}")
    print(f"wrote {out_dir / 'simulation_results_by_epsilon_detailed.csv'}")
    print(f"wrote {out_dir / 'lambda_summary_by_epsilon.csv'}")
    print(f"wrote {out_dir / 'final_bounds_check.csv'}")
    print(f"wrote {out_dir / 'Fig7_epsilon_ET.png'}")
    print(f"wrote {out_dir / 'Fig7_epsilon_ET.eps'}")
    print(f"wrote {out_dir / 'Fig3_epsilon_ET.png'}")
    print(f"wrote {out_dir / 'Fig3_epsilon_ET.eps'}")


if __name__ == "__main__":
    main()
