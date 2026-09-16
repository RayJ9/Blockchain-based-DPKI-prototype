from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .backend import (
    POW_RUNTIME,
    ROOT,
    ModelParams,
    RunSpec,
    pki_theory_value,
    run_real_experiment,
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)


POW_SCRIPTS = ROOT / "blockchain" / "pow-4nodes-runtime" / "scripts"
SIDECHAIN_SCRIPTS = ROOT / "blockchain" / "sidechain-three-chain" / "scripts"
DEFAULT_EPSILON_POINTS = [round(float(x), 2) for x in np.arange(0.0, 0.6001, 0.05)]
FINAL_OUTPUT_FILES = [
    "figure.png",
    "figure.eps",
    "figure_data.csv",
    "delay_by_request_type.csv",
    "manifest.json",
]
LEGACY_OUTPUT_FILES = [
    "epsilon_cached_experiment.png",
    "epsilon_cached_experiment.eps",
    "epsilon_cached_experiment_points.csv",
    "epsilon_cached_experiment_smooth.csv",
    "epsilon_cached_experiment_delay_by_kind.csv",
    "manifest_epsilon_cached_experiment.json",
]
LOG_FILE_MAP = [
    ("run.log", "run.log"),
    ("run_config.json", "config.json"),
    ("real_chain_observation.json", "chain_observation.json"),
    ("real_chain_tx_breakdown.csv", "chain_transactions.csv"),
    ("measured_parameters.json", "parameters.json"),
    ("real_summary_by_epsilon_detailed.csv", "summary_by_epsilon.csv"),
    ("real_simulation_results_by_epsilon_detailed.csv", "request_samples.csv"),
    ("exact_bounds_check_latest.csv", "source_bounds_check.csv"),
]
PLOT_SERIES = [
    ("DPKI_upper_theory", "DPKI_upper_bound", "DPKI Upper Bound", "-", (0.0, 0.5, 0.0), True, None),
    ("DPKI_lower_theory", "DPKI_lower_bound", "DPKI Lower Bound", "-", (0.0, 0.447, 0.741), True, None),
    ("DPKI_sim", "DPKI_experimental", "DPKI Experimental", "--", (1.0, 0.4, 0.0), True, "o"),
    ("PKI_theory", "PKI_theory", "PKI Theory", "-", (0.85, 0.0, 0.0), True, None),
    ("PKI_sim", "PKI_experimental", "PKI Experimental", "", (0.85, 0.0, 0.0), False, "D"),
]


def run_powershell(script: Path, args: list[str]) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def restart_pow(mean_block_ms: int) -> None:
    if os.environ.get("DPKI_USE_SIDECHAINS", "").lower() in {"1", "true", "yes", "on"}:
        run_powershell(SIDECHAIN_SCRIPTS / "stop-three-chains.ps1", [])
        run_powershell(SIDECHAIN_SCRIPTS / "start-three-chains.ps1", ["-MeanBlockMs", str(mean_block_ms)])
        time.sleep(30)
        return
    run_powershell(POW_SCRIPTS / "stop-omnilink-pow-4nodes.ps1", [])
    ready = POW_RUNTIME / "ready.txt"
    if ready.exists():
        ready.unlink()
    run_powershell(
        POW_SCRIPTS / "start-omnilink-pow-4nodes.ps1",
        ["-MeanBlockMs", str(mean_block_ms), "-MineEmpty", "-AggregateMiningOnNode0", "-WarmupSeconds", "10"],
    )
    time.sleep(30)


def stop_pow() -> None:
    if os.environ.get("DPKI_USE_SIDECHAINS", "").lower() in {"1", "true", "yes", "on"}:
        run_powershell(SIDECHAIN_SCRIPTS / "stop-three-chains.ps1", [])
        return
    run_powershell(POW_SCRIPTS / "stop-omnilink-pow-4nodes.ps1", [])


def epsilon_text(values: list[float] | float) -> str:
    if isinstance(values, (int, float)):
        return f"{float(values):.2f}".rstrip("0").rstrip(".")
    return ",".join(f"{float(value):.2f}".rstrip("0").rstrip(".") for value in values)


def theory_from_params(params: ModelParams, epsilon: float) -> dict[str, float]:
    upper = theoretical_values_dpki_upper_bound(
        params.lambda_total,
        params.p_manage,
        params.q_manage,
        params.mu,
        params.service_cas,
        params.gamma_on_chain,
        params.lambda_block,
        epsilon,
    )
    lower = theoretical_values_dpki_lower_bound(
        params.lambda_total,
        params.p_manage,
        params.q_manage,
        params.mu,
        params.service_cas,
        params.gamma_on_chain,
        params.lambda_block,
        epsilon,
    )
    pki_theory, pki_rho = pki_theory_value(params, epsilon)
    return {
        "DPKI_upper_theory": float(upper["E_T_total"]),
        "DPKI_lower_theory": float(lower["E_T_total"]),
        "PKI_theory": float(pki_theory),
        "PKI_rho": float(pki_rho),
    }


def build_points(run_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate unchanged request measurements; theory never changes a sample."""
    metadata = json.loads((run_dir / "measured_parameters.json").read_text(encoding="utf8"))
    detailed = pd.read_csv(run_dir / "real_simulation_results_by_epsilon_detailed.csv")
    required = {"epsilon", "model", "kind", "onChain", "serviceMs", "queueMs", "latencyMs", "arrivalWallMs"}
    missing = required - set(detailed.columns)
    if missing:
        raise ValueError(f"Missing request measurements: {sorted(missing)}")
    for column in ("epsilon", "serviceMs", "queueMs", "latencyMs", "arrivalWallMs"):
        detailed[column] = pd.to_numeric(detailed[column], errors="raise")
        if not np.isfinite(detailed[column]).all():
            raise ValueError(f"Non-finite request measurements in {column}")
    if (detailed[["serviceMs", "queueMs", "latencyMs"]] < 0).any().any():
        raise ValueError("Negative measured request duration")
    service_cas = int(metadata["serviceCAs"])
    block_rate = metadata.get("lambdaBlockMeasured")
    block_rate = float(block_rate) if block_rate is not None else float("nan")
    rows, kind_rows = [], []

    def mean_service(frame: pd.DataFrame, kind: str) -> float:
        return float(frame.loc[frame["kind"] == kind, "serviceMs"].mean() / 1000.0)

    for epsilon, group in detailed.groupby("epsilon", sort=True):
        dpki = group[group["model"] == "DPKI"]
        pki = group[group["model"] == "PKI"]
        if dpki.empty:
            raise ValueError(f"No DPKI requests at epsilon={epsilon}")
        span = (dpki["arrivalWallMs"].max() - dpki["arrivalWallMs"].min()) / 1000.0
        arrival_rate = (len(dpki) - 1) / span if span > 0 else float("nan")
        p_manage = float((dpki["kind"] == "management").mean())
        normal = dpki[dpki["kind"].isin(["intra-on-chain", "intra-off-chain"])]
        gamma = float((normal["kind"] == "intra-on-chain").mean())
        auth_sec = mean_service(dpki, "intra-off-chain")
        management_sec = mean_service(dpki, "management")
        mu = 1.0 / auth_sec if auth_sec > 0 else float("nan")
        # If no management request was scheduled, q is irrelevant to that point.
        q = auth_sec / management_sec if management_sec > 0 else (1.0 if p_manage == 0 else float("nan"))
        pki_auth_sec = mean_service(pki, "intra-pki")
        pki_management_sec = mean_service(pki, "management")
        pki_mu = 1.0 / pki_auth_sec if pki_auth_sec > 0 else float("nan")
        pki_q = pki_auth_sec / pki_management_sec if pki_management_sec > 0 else (1.0 if not (pki["kind"] == "management").any() else float("nan"))
        theory = dict.fromkeys(["DPKI_upper_theory", "DPKI_lower_theory", "PKI_theory", "PKI_rho"], float("nan"))
        if all(math.isfinite(value) and value > 0 for value in (arrival_rate, mu, q, block_rate)) and math.isfinite(gamma):
            params = ModelParams(lambda_total=arrival_rate, p_manage=p_manage, q_manage=q,
                                 mu=mu, service_cas=service_cas, gamma_on_chain=gamma,
                                 lambda_block=block_rate, pki_mu=pki_mu,
                                 pki_q_manage=pki_q, pki_cross_extra_mu=pki_mu)
            theory = theory_from_params(params, float(epsilon))
        rows.append({
            "epsilon": float(epsilon),
            "DPKI_sim": float(dpki["latencyMs"].mean() / 1000.0),
            "PKI_sim": float(pki["latencyMs"].mean() / 1000.0),
            "lambdaTotalMeasured": arrival_rate, "pManageMeasured": p_manage,
            "gammaOnChainMeasured": gamma, "qManageMeasured": q,
            "muModelOffchainAuthMeasured": mu, "lambdaBlockMeasured": block_rate,
            "lambdaBlockHeightMeasured": block_rate, "serviceCAs": service_cas,
            "pkiMuPrimaryAuthMeasured": pki_mu, "pkiQManageMeasured": pki_q,
            "measurementScope": "pointwise observed rates; unchanged request durations", **theory,
        })
        for (model, kind), requests in group.groupby(["model", "kind"]):
            kind_rows.append({
                "epsilon": float(epsilon), "model": model, "kind": kind, "count": len(requests),
                "originalLatencyMs": float(requests["latencyMs"].mean()),
                "originalServiceMs": float(requests["serviceMs"].mean()),
                "figLatencyMs": float(requests["latencyMs"].mean()),
                "figServiceMs": float(requests["serviceMs"].mean()),
                "figQueueMs": float(requests["queueMs"].mean()),
            })
    return pd.DataFrame(rows), pd.DataFrame(kind_rows)


def plot(points: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, _, label, style, color, show_line, marker in PLOT_SERIES:
        frame = points[["epsilon", column]].replace([np.inf, -np.inf], np.nan).sort_values("epsilon")
        ax.plot(frame["epsilon"], frame[column], color=color, linestyle=style or "none",
                marker=marker or "", markerfacecolor="none", linewidth=1.5, label=label)
    ax.set_xlabel(r"$\epsilon$")
    ax.set_ylabel(r"$E[T]$ (s)")
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)
    return points.copy()


def write_figure_data(points: pd.DataFrame, plotted: pd.DataFrame, output_dir: Path) -> None:
    rename_map = {source: clean for source, clean, *_ in PLOT_SERIES}
    raw = points.rename(columns=rename_map).copy()
    raw.insert(0, "dataKind", "measured_point")
    raw.to_csv(output_dir / "figure_data.csv", index=False)


def cleanup_legacy_outputs(directory: Path) -> None:
    for name in LEGACY_OUTPUT_FILES:
        path = directory / name
        if path.exists():
            path.unlink()


def mirror_final_outputs_to_script_root(output_dir: Path, script_dir: Path) -> None:
    cleanup_legacy_outputs(script_dir)
    for name in FINAL_OUTPUT_FILES:
        source = output_dir / name
        if source.exists():
            shutil.copy2(source, script_dir / name)


def copy_run_logs(run_dir: Path, output_dir: Path) -> Path:
    logs_dir = output_dir / "logs"
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
    logs_dir.mkdir(parents=True)
    copied: list[dict[str, str]] = []
    for source_name, dest_name in LOG_FILE_MAP:
        source = run_dir / source_name
        if source.exists():
            shutil.copy2(source, logs_dir / dest_name)
            copied.append({"source": source_name, "savedAs": dest_name})
    latency_frames: list[pd.DataFrame] = []
    for source_name, level in [
        ("real_delay_statistics.csv", "request_type"),
        ("real_stage_statistics.csv", "stage"),
    ]:
        source = run_dir / source_name
        if source.exists():
            frame = pd.read_csv(source)
            frame.insert(0, "level", level)
            latency_frames.append(frame)
    if latency_frames:
        pd.concat(latency_frames, ignore_index=True, sort=False).to_csv(logs_dir / "latency_statistics.csv", index=False)
        copied.append(
            {
                "source": "real_delay_statistics.csv + real_stage_statistics.csv",
                "savedAs": "latency_statistics.csv",
            }
        )
    (logs_dir / "source_run_dir.txt").write_text(f"{run_dir}\n", encoding="utf8")
    (logs_dir / "log_manifest.json").write_text(json.dumps(copied, indent=2), encoding="utf8")
    return logs_dir


def write_bounds_check(points: pd.DataFrame, logs_dir: Path) -> pd.DataFrame:
    check = points.copy()
    check["DPKI_in_bounds"] = (
        (check["DPKI_sim"] >= check["DPKI_lower_theory"])
        & (check["DPKI_sim"] <= check["DPKI_upper_theory"])
    )
    check["DPKI_minus_lower"] = check["DPKI_sim"] - check["DPKI_lower_theory"]
    check["DPKI_minus_upper"] = check["DPKI_sim"] - check["DPKI_upper_theory"]
    check["PKI_abs_error"] = (check["PKI_sim"] - check["PKI_theory"]).abs()
    check["PKI_signed_error"] = check["PKI_sim"] - check["PKI_theory"]
    check.to_csv(logs_dir / "bounds_check.csv", index=False)
    return check


def load_run_spec(run_dir: Path) -> dict[str, object]:
    config_path = run_dir / "run_config.json"
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf8"))
    except json.JSONDecodeError:
        return {}
    spec = data.get("spec", {})
    return spec if isinstance(spec, dict) else {}


def run_experiment_from_args(args) -> Path:
    return run_real_experiment(
        RunSpec(
            label=args.tag or "result",
            sweep="cross-domain-ratio",
            x_name="epsilon",
            x_value=0.0,
            epsilon_points=epsilon_text(args.epsilon_values),
            requests=args.requests,
            lambda_arrival=args.lambda_arrival,
            p_manage=args.p_manage,
            gamma_on_chain=args.gamma_on_chain,
            q_manage=args.q_manage,
            service_cas=args.service_cas,
            fixed_gas_limit=args.fixed_gas_limit,
            fixed_gas_price_wei=str(args.fixed_gas_price_wei),
            raw_tx_submit_timeout_ms=args.raw_tx_submit_timeout_ms,
            raw_tx_submit_retries=args.raw_tx_submit_retries,
            raw_tx_receipt_timeout_ms=args.raw_tx_receipt_timeout_ms,
            lambda_block=args.lambda_block,
            arrival_mode="wall",
            kind_plan_mode="fixed",
            dpki_root_read_mode=args.dpki_root_read_mode,
            dpki_proof_read_mode=args.dpki_proof_read_mode,
            dpki_proof_base_port=args.dpki_proof_base_port,
            actual_execution_mode=args.actual_execution_mode,
            seed=args.seed,
        )
    )
