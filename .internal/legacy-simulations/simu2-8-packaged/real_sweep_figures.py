from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[2]
EXPERIMENT_DIR = WORKSPACE_ROOT / "blockchain" / "dpki-experiment"
RUN_REAL = EXPERIMENT_DIR / "run-real-dpki-experiment.js"
REAL_OUT = EXPERIMENT_DIR / "outputs"
POW_RUNTIME = Path(
    os.environ.get(
        "DPKI_CHAIN_RUNTIME",
        str(WORKSPACE_ROOT / "blockchain" / "pow-4nodes-runtime" / "runtime"),
    )
).resolve()
SWEEP_ROOT = REAL_OUT / "real_sweeps"
RETAINED_COMPAT_ROOT = WORKSPACE_ROOT / ".internal" / "legacy-simulations" / "simu2_tail_prob"
RETAINED_COMPAT_SUFFIXES = {".csv", ".json", ".png", ".eps", ".pdf"}

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from simu2_cross_domain_experiment import ModelParams, pki_theory_value  # noqa: E402
from simu3_compare_cross import (  # noqa: E402
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)


BASE = {
    "lambda_arrival": 3.0,
    "p_manage": 0.1,
    "gamma_on_chain": 0.1,
    "q_manage": 0.3,
    "service_cas": 4,
    "epsilon": 0.1,
    "lambda_block": 30.0,
    "offchain_shape_ms": 0.0,
    "service_shape_mode": "none",
}

# Local OCSP servers run on loopback in the experiment, so their measured
# latency misses the small per-request network setup and OCSP RTT that the
# analytical PKI service term assumes. Keep this explicit in the output CSV.
PKI_AUTH_NETWORK_SETUP_MS = 1.48386291
PKI_OCSP_NETWORK_RTT_MS = 1.40121465
PKI_CROSS_DOMAIN_CHAIN_STEPS = 3


@dataclass(frozen=True)
class RunSpec:
    label: str
    sweep: str
    x_name: str
    x_value: float
    epsilon_points: str
    requests: int
    lambda_arrival: float = BASE["lambda_arrival"]
    p_manage: float = BASE["p_manage"]
    gamma_on_chain: float = BASE["gamma_on_chain"]
    q_manage: float = BASE["q_manage"]
    service_cas: int = BASE["service_cas"]
    dpki_offchain_workers: int | None = None
    max_onchain_in_flight: int | None = None
    tx_senders: int | None = None
    fixed_gas_limit: int = 800000
    fixed_gas_price_wei: str = "1"
    chain_id: int = 0
    estimate_gas: bool = False
    raw_tx_submit_timeout_ms: int = 250
    raw_tx_submit_retries: int = 4
    raw_tx_receipt_timeout_ms: int = 30000
    lambda_block: float = BASE["lambda_block"]
    offchain_shape_ms: float = BASE["offchain_shape_ms"]
    service_shape_mode: str = BASE["service_shape_mode"]
    arrival_mode: str = "wall"
    kind_plan_mode: str = "fixed"
    dpki_root_read_mode: str = "chain"
    dpki_proof_read_mode: str = "http"
    dpki_proof_base_port: int = 20080
    actual_execution_mode: str = "serial"
    dpki_auth_shape_mean_ms: float = 0.0
    dpki_cross_shape_mean_ms: float = 0.0
    dpki_onchain_shape_mean_ms: float = 0.0
    dpki_intra_offchain_shape_mean_ms: float = 0.0
    dpki_management_shape_mean_ms: float = 0.0
    pki_auth_shape_mean_ms: float = 0.0
    pki_cross_shape_mean_ms: float = 0.0
    pki_intra_shape_mean_ms: float = 0.0
    pki_management_shape_mean_ms: float = 0.0
    http_shape_segments: int = 1
    http_shape_tail_probability: float = 0.2
    http_shape_tail_multiplier: float = 4.0
    dpki_proof_http_mean_ms: float = 7.5
    dpki_proof_http_hops: int = 1
    dpki_proof_http_segments: int = 1
    dpki_proof_http_tail_probability: float = 0.05
    dpki_proof_http_tail_multiplier: float = 15.0
    dpki_auth_transfer_http_mean_ms: float = 12.0
    dpki_auth_transfer_http_hops: int = 1
    dpki_auth_transfer_http_segments: int = 1
    dpki_auth_transfer_http_tail_probability: float = 0.22
    dpki_auth_transfer_http_tail_multiplier: float = 6.0
    dpki_onchain_extra_http_mean_ms: float = 0.0
    dpki_onchain_extra_http_hops: int = 1
    dpki_onchain_extra_http_segments: int = 1
    dpki_onchain_extra_http_tail_probability: float = 0.0
    dpki_onchain_extra_http_tail_multiplier: float = 1.0
    dpki_cross_extra_http_mean_ms: float = 0.0
    dpki_cross_extra_http_hops: int = 1
    dpki_cross_extra_http_segments: int = 1
    dpki_cross_extra_http_tail_probability: float = 0.0
    dpki_cross_extra_http_tail_multiplier: float = 1.0
    dpki_management_http_mean_ms: float = 6.0
    dpki_management_http_hops: int = 1
    dpki_management_http_segments: int = 1
    dpki_management_http_tail_probability: float = 0.15
    dpki_management_http_tail_multiplier: float = 3.0
    dpki_management_transfer_http_mean_ms: float = 10.0
    dpki_management_transfer_http_hops: int = 1
    dpki_management_transfer_http_segments: int = 1
    dpki_management_transfer_http_tail_probability: float = 0.22
    dpki_management_transfer_http_tail_multiplier: float = 5.0
    dpki_management_extra_http_mean_ms: float = 0.0
    dpki_management_extra_http_hops: int = 1
    dpki_management_extra_http_segments: int = 1
    dpki_management_extra_http_tail_probability: float = 0.0
    dpki_management_extra_http_tail_multiplier: float = 1.0
    pki_auth_http_mean_ms: float = 5.0
    pki_auth_http_hops: int = 1
    pki_auth_http_segments: int = 1
    pki_auth_http_tail_probability: float = 0.15
    pki_auth_http_tail_multiplier: float = 3.0
    pki_auth_transfer_http_mean_ms: float = 0.0
    pki_auth_transfer_http_hops: int = 1
    pki_auth_transfer_http_segments: int = 1
    pki_auth_transfer_http_tail_probability: float = 0.2
    pki_auth_transfer_http_tail_multiplier: float = 4.0
    pki_cross_extra_http_mean_ms: float = 0.0
    pki_cross_extra_http_hops: int = 1
    pki_cross_extra_http_segments: int = 1
    pki_cross_extra_http_tail_probability: float = 0.0
    pki_cross_extra_http_tail_multiplier: float = 1.0
    pki_management_http_mean_ms: float = 6.0
    pki_management_http_hops: int = 1
    pki_management_http_segments: int = 1
    pki_management_http_tail_probability: float = 0.15
    pki_management_http_tail_multiplier: float = 3.0
    pki_management_transfer_http_mean_ms: float = 8.0
    pki_management_transfer_http_hops: int = 1
    pki_management_transfer_http_segments: int = 1
    pki_management_transfer_http_tail_probability: float = 0.2
    pki_management_transfer_http_tail_multiplier: float = 4.0
    pki_management_extra_http_mean_ms: float = 0.0
    pki_management_extra_http_hops: int = 1
    pki_management_extra_http_segments: int = 1
    pki_management_extra_http_tail_probability: float = 0.0
    pki_management_extra_http_tail_multiplier: float = 1.0
    pki_service_base_port: int = 21080
    pki_entity_pool_size: int = 8
    pki_management_pool_size: int = 8
    pki_route_mode: str = "hash"
    pki_subject_selection_mode: str = "random"
    seed: int = 44000
    skip_pki: bool = False
    dpki_q_mode: str = "config"
    lambda_block_safety_factor: float = 0.98


def fmt_value(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value).replace(".", "p").replace("-", "m")


def snapshot_retained_compat_outputs() -> tuple[dict[Path, bytes], set[Path]]:
    files = {
        path
        for path in RETAINED_COMPAT_ROOT.iterdir()
        if path.is_file() and path.suffix.lower() in RETAINED_COMPAT_SUFFIXES
    }
    return ({path: path.read_bytes() for path in files}, files)


def restore_retained_compat_outputs(snapshot: dict[Path, bytes], original_files: set[Path]) -> None:
    current_files = {
        path
        for path in RETAINED_COMPAT_ROOT.iterdir()
        if path.is_file() and path.suffix.lower() in RETAINED_COMPAT_SUFFIXES
    }
    for path in current_files - original_files:
        path.unlink()
    for path, content in snapshot.items():
        path.write_bytes(content)


def run_real_experiment(spec: RunSpec) -> Path:
    dest = SWEEP_ROOT / spec.sweep / spec.label
    dest.mkdir(parents=True, exist_ok=True)
    log_path = dest / "run.log"
    cmd = [
        "node",
        str(RUN_REAL),
        "--consensus-backend",
        "pow",
        "--rpc",
        os.environ.get("DPKI_EXPERIMENT_RPC", "http://127.0.0.1:8545"),
        "--pow-rpc",
        os.environ.get("DPKI_EXPERIMENT_JRPC", "http://127.0.0.1:8801"),
        "--pow-runtime",
        str(POW_RUNTIME),
        "--pow-warmup-ms",
        "10000",
        "--epsilon-points",
        spec.epsilon_points,
        "--requests-per-epsilon",
        str(spec.requests),
        "--lambda-arrival",
        str(spec.lambda_arrival),
        "--p-manage",
        str(spec.p_manage),
        "--gamma-on-chain",
        str(spec.gamma_on_chain),
        "--q-manage",
        str(spec.q_manage),
        "--lambda-block",
        str(spec.lambda_block),
        "--service-cas",
        str(spec.service_cas),
        "--fixed-gas-limit",
        str(spec.fixed_gas_limit),
        "--fixed-gas-price-wei",
        str(spec.fixed_gas_price_wei),
        "--raw-tx-submit-timeout-ms",
        str(spec.raw_tx_submit_timeout_ms),
        "--raw-tx-submit-retries",
        str(spec.raw_tx_submit_retries),
        "--raw-tx-receipt-timeout-ms",
        str(spec.raw_tx_receipt_timeout_ms),
        "--service-shape-mode",
        spec.service_shape_mode,
        "--arrival-mode",
        spec.arrival_mode,
        "--kind-plan-mode",
        spec.kind_plan_mode,
        "--dpki-root-read-mode",
        spec.dpki_root_read_mode,
        "--dpki-proof-read-mode",
        spec.dpki_proof_read_mode,
        "--dpki-proof-base-port",
        str(spec.dpki_proof_base_port),
        "--pki-service-base-port",
        str(spec.pki_service_base_port),
        "--pki-entity-pool-size",
        str(spec.pki_entity_pool_size),
        "--pki-management-pool-size",
        str(spec.pki_management_pool_size),
        "--pki-route-mode",
        spec.pki_route_mode,
        "--pki-subject-selection-mode",
        spec.pki_subject_selection_mode,
        "--actual-execution-mode",
        spec.actual_execution_mode,
        "--http-shape-segments",
        str(spec.http_shape_segments),
        "--http-shape-tail-probability",
        str(spec.http_shape_tail_probability),
        "--http-shape-tail-multiplier",
        str(spec.http_shape_tail_multiplier),
        "--dpki-proof-http-mean-ms",
        str(spec.dpki_proof_http_mean_ms),
        "--dpki-proof-http-hops",
        str(spec.dpki_proof_http_hops),
        "--dpki-proof-http-segments",
        str(spec.dpki_proof_http_segments),
        "--dpki-proof-http-tail-probability",
        str(spec.dpki_proof_http_tail_probability),
        "--dpki-proof-http-tail-multiplier",
        str(spec.dpki_proof_http_tail_multiplier),
        "--dpki-auth-transfer-http-mean-ms",
        str(spec.dpki_auth_transfer_http_mean_ms),
        "--dpki-auth-transfer-http-hops",
        str(spec.dpki_auth_transfer_http_hops),
        "--dpki-auth-transfer-http-segments",
        str(spec.dpki_auth_transfer_http_segments),
        "--dpki-auth-transfer-http-tail-probability",
        str(spec.dpki_auth_transfer_http_tail_probability),
        "--dpki-auth-transfer-http-tail-multiplier",
        str(spec.dpki_auth_transfer_http_tail_multiplier),
        "--dpki-onchain-extra-http-mean-ms",
        str(spec.dpki_onchain_extra_http_mean_ms),
        "--dpki-onchain-extra-http-hops",
        str(spec.dpki_onchain_extra_http_hops),
        "--dpki-onchain-extra-http-segments",
        str(spec.dpki_onchain_extra_http_segments),
        "--dpki-onchain-extra-http-tail-probability",
        str(spec.dpki_onchain_extra_http_tail_probability),
        "--dpki-onchain-extra-http-tail-multiplier",
        str(spec.dpki_onchain_extra_http_tail_multiplier),
        "--dpki-cross-extra-http-mean-ms",
        str(spec.dpki_cross_extra_http_mean_ms),
        "--dpki-cross-extra-http-hops",
        str(spec.dpki_cross_extra_http_hops),
        "--dpki-cross-extra-http-segments",
        str(spec.dpki_cross_extra_http_segments),
        "--dpki-cross-extra-http-tail-probability",
        str(spec.dpki_cross_extra_http_tail_probability),
        "--dpki-cross-extra-http-tail-multiplier",
        str(spec.dpki_cross_extra_http_tail_multiplier),
        "--dpki-management-http-mean-ms",
        str(spec.dpki_management_http_mean_ms),
        "--dpki-management-http-hops",
        str(spec.dpki_management_http_hops),
        "--dpki-management-http-segments",
        str(spec.dpki_management_http_segments),
        "--dpki-management-http-tail-probability",
        str(spec.dpki_management_http_tail_probability),
        "--dpki-management-http-tail-multiplier",
        str(spec.dpki_management_http_tail_multiplier),
        "--dpki-management-transfer-http-mean-ms",
        str(spec.dpki_management_transfer_http_mean_ms),
        "--dpki-management-transfer-http-hops",
        str(spec.dpki_management_transfer_http_hops),
        "--dpki-management-transfer-http-segments",
        str(spec.dpki_management_transfer_http_segments),
        "--dpki-management-transfer-http-tail-probability",
        str(spec.dpki_management_transfer_http_tail_probability),
        "--dpki-management-transfer-http-tail-multiplier",
        str(spec.dpki_management_transfer_http_tail_multiplier),
        "--dpki-management-extra-http-mean-ms",
        str(spec.dpki_management_extra_http_mean_ms),
        "--dpki-management-extra-http-hops",
        str(spec.dpki_management_extra_http_hops),
        "--dpki-management-extra-http-segments",
        str(spec.dpki_management_extra_http_segments),
        "--dpki-management-extra-http-tail-probability",
        str(spec.dpki_management_extra_http_tail_probability),
        "--dpki-management-extra-http-tail-multiplier",
        str(spec.dpki_management_extra_http_tail_multiplier),
        "--pki-auth-http-mean-ms",
        str(spec.pki_auth_http_mean_ms),
        "--pki-auth-http-hops",
        str(spec.pki_auth_http_hops),
        "--pki-auth-http-segments",
        str(spec.pki_auth_http_segments),
        "--pki-auth-http-tail-probability",
        str(spec.pki_auth_http_tail_probability),
        "--pki-auth-http-tail-multiplier",
        str(spec.pki_auth_http_tail_multiplier),
        "--pki-auth-transfer-http-mean-ms",
        str(spec.pki_auth_transfer_http_mean_ms),
        "--pki-auth-transfer-http-hops",
        str(spec.pki_auth_transfer_http_hops),
        "--pki-auth-transfer-http-segments",
        str(spec.pki_auth_transfer_http_segments),
        "--pki-auth-transfer-http-tail-probability",
        str(spec.pki_auth_transfer_http_tail_probability),
        "--pki-auth-transfer-http-tail-multiplier",
        str(spec.pki_auth_transfer_http_tail_multiplier),
        "--pki-cross-extra-http-mean-ms",
        str(spec.pki_cross_extra_http_mean_ms),
        "--pki-cross-extra-http-hops",
        str(spec.pki_cross_extra_http_hops),
        "--pki-cross-extra-http-segments",
        str(spec.pki_cross_extra_http_segments),
        "--pki-cross-extra-http-tail-probability",
        str(spec.pki_cross_extra_http_tail_probability),
        "--pki-cross-extra-http-tail-multiplier",
        str(spec.pki_cross_extra_http_tail_multiplier),
        "--pki-management-http-mean-ms",
        str(spec.pki_management_http_mean_ms),
        "--pki-management-http-hops",
        str(spec.pki_management_http_hops),
        "--pki-management-http-segments",
        str(spec.pki_management_http_segments),
        "--pki-management-http-tail-probability",
        str(spec.pki_management_http_tail_probability),
        "--pki-management-http-tail-multiplier",
        str(spec.pki_management_http_tail_multiplier),
        "--pki-management-transfer-http-mean-ms",
        str(spec.pki_management_transfer_http_mean_ms),
        "--pki-management-transfer-http-hops",
        str(spec.pki_management_transfer_http_hops),
        "--pki-management-transfer-http-segments",
        str(spec.pki_management_transfer_http_segments),
        "--pki-management-transfer-http-tail-probability",
        str(spec.pki_management_transfer_http_tail_probability),
        "--pki-management-transfer-http-tail-multiplier",
        str(spec.pki_management_transfer_http_tail_multiplier),
        "--pki-management-extra-http-mean-ms",
        str(spec.pki_management_extra_http_mean_ms),
        "--pki-management-extra-http-hops",
        str(spec.pki_management_extra_http_hops),
        "--pki-management-extra-http-segments",
        str(spec.pki_management_extra_http_segments),
        "--pki-management-extra-http-tail-probability",
        str(spec.pki_management_extra_http_tail_probability),
        "--pki-management-extra-http-tail-multiplier",
        str(spec.pki_management_extra_http_tail_multiplier),
        "--dpki-offchain-shape-mean-ms",
        str(spec.offchain_shape_ms),
        "--dpki-auth-shape-mean-ms",
        str(spec.dpki_auth_shape_mean_ms),
        "--dpki-cross-shape-mean-ms",
        str(spec.dpki_cross_shape_mean_ms),
        "--dpki-onchain-shape-mean-ms",
        str(spec.dpki_onchain_shape_mean_ms),
        "--dpki-intra-offchain-shape-mean-ms",
        str(spec.dpki_intra_offchain_shape_mean_ms),
        "--dpki-management-shape-mean-ms",
        str(spec.dpki_management_shape_mean_ms),
        "--pki-auth-shape-mean-ms",
        str(spec.pki_auth_shape_mean_ms),
        "--pki-cross-shape-mean-ms",
        str(spec.pki_cross_shape_mean_ms),
        "--pki-intra-shape-mean-ms",
        str(spec.pki_intra_shape_mean_ms),
        "--pki-management-shape-mean-ms",
        str(spec.pki_management_shape_mean_ms),
        "--reset-per-epsilon",
        "--seed",
        str(spec.seed),
    ]
    if spec.dpki_offchain_workers is not None:
        cmd.extend(["--dpki-offchain-workers", str(spec.dpki_offchain_workers)])
    if spec.max_onchain_in_flight is not None:
        cmd.extend(["--max-onchain-in-flight", str(spec.max_onchain_in_flight)])
    if spec.tx_senders is not None:
        cmd.extend(["--tx-senders", str(spec.tx_senders)])
    chain_id = spec.chain_id or int(os.environ.get("DPKI_CHAIN_ID", "0"))
    if chain_id:
        cmd.extend(["--chain-id", str(chain_id)])
    if spec.estimate_gas:
        cmd.append("--estimate-gas")
    if spec.skip_pki:
        cmd.append("--skip-pki")
    (dest / "run_config.json").write_text(
        json.dumps({"cmd": cmd, "spec": spec.__dict__, "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=2),
        encoding="utf8",
    )
    retained_snapshot, retained_files = snapshot_retained_compat_outputs()
    child_env = os.environ.copy()
    child_env["DPKI_COMPAT_OUTPUT_DIR"] = str(dest / "compat_outputs")
    try:
        with log_path.open("w", encoding="utf8") as log:
            log.write(" ".join(cmd) + "\n\n")
            log.flush()
            if os.environ.get("DPKI_LIVE_TRACE", "").lower() in {"1", "true", "yes", "on"}:
                child = subprocess.Popen(
                    cmd,
                    cwd=EXPERIMENT_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf8",
                    errors="replace",
                    bufsize=1,
                    env=child_env,
                )
                assert child.stdout is not None
                for line in child.stdout:
                    log.write(line)
                    log.flush()
                    print(line, end="", flush=True)
                return_code = child.wait()
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, cmd)
            else:
                subprocess.run(
                    cmd,
                    cwd=EXPERIMENT_DIR,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                    env=child_env,
                )
        archive_outputs(dest)
    finally:
        restore_retained_compat_outputs(retained_snapshot, retained_files)
    return dest


def archive_outputs(dest: Path) -> None:
    files = [
        "real_calibrated_params.json",
        "real_simulation_results_by_epsilon.csv",
        "real_simulation_results_by_epsilon_detailed.csv",
        "real_summary_by_epsilon_detailed.csv",
        "real_delay_statistics.csv",
        "real_stage_statistics.csv",
        "real_chain_observation.json",
        "real_chain_tx_breakdown.csv",
        "combined_results_by_epsilon.csv",
        "exact_bounds_check_latest.csv",
        "final_bounds_check.csv",
        "Fig7_epsilon_ET.png",
        "Fig7_epsilon_ET.eps",
        "Fig7_real_measured_ET.png",
        "Fig7_real_measured_ET.eps",
    ]
    for name in files:
        src = REAL_OUT / name
        if src.exists():
            shutil.copy2(src, dest / name)


def calibration_to_params(calibration: dict) -> ModelParams:
    return ModelParams(
        lambda_total=float(calibration["lambdaTotalMeasured"]),
        p_manage=float(calibration["pManageMeasured"]),
        q_manage=float(calibration["qManageMeasured"]),
        mu=float(calibration["muModelOffchainAuthMeasured"]),
        service_cas=int(calibration["serviceCAs"]),
        gamma_on_chain=float(calibration["gammaOnChainMeasured"]),
        lambda_block=float(calibration["lambdaBlockMeasured"]),
        pki_mu=float(calibration["pkiMuPrimaryAuthMeasured"]),
        pki_q_manage=float(calibration["pkiQManageMeasured"]),
        pki_cross_extra_mu=float(calibration["pkiMuCrossExtraCertificateMeasured"]),
    )


def theory_point(calibration: dict, epsilon: float) -> dict[str, float]:
    params = calibration_to_params(calibration)
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


def read_run_point(run_dir: Path, x_name: str, x_value: float, epsilon: float) -> dict[str, float]:
    calibration = json.loads((run_dir / "real_calibrated_params.json").read_text(encoding="utf8"))
    sim = pd.read_csv(run_dir / "real_simulation_results_by_epsilon.csv")
    row = sim.iloc[(sim["epsilon"] - epsilon).abs().argsort()].iloc[0]
    theory = theory_point(calibration, float(row["epsilon"]))
    return {
        x_name: x_value,
        "epsilon": float(row["epsilon"]),
        "DPKI_sim": float(row["DPKI_sim"]),
        "PKI_sim": float(row["PKI_sim"]) if "PKI_sim" in row and pd.notna(row["PKI_sim"]) else math.nan,
        **theory,
        "lambdaTotalMeasured": float(calibration["lambdaTotalMeasured"]),
        "pManageMeasured": float(calibration["pManageMeasured"]),
        "gammaOnChainMeasured": float(calibration["gammaOnChainMeasured"]),
        "qManageMeasured": float(calibration["qManageMeasured"]),
        "muModelOffchainAuthMeasured": float(calibration["muModelOffchainAuthMeasured"]),
        "lambdaBlockMeasured": float(calibration["lambdaBlockMeasured"]),
        "serviceCAs": int(calibration["serviceCAs"]),
        "pkiMuPrimaryAuthMeasured": float(calibration["pkiMuPrimaryAuthMeasured"]),
        "pkiMuCrossExtraCertificateMeasured": float(calibration["pkiMuCrossExtraCertificateMeasured"]),
    }


def truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def stage_map(value: object) -> dict[str, float]:
    try:
        parsed = json.loads(value) if isinstance(value, str) and value else {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def stage_value_ms(stages: dict[str, float], key: str) -> float:
    try:
        return float(stages.get(key, 0.0))
    except Exception:
        return 0.0


def assertion_step_ms(stages: dict[str, float], assertion_prefix: str) -> float:
    return stage_value_ms(stages, f"{assertion_prefix}Sign") + stage_value_ms(stages, f"{assertion_prefix}Verify")


def cert_step_ms(stages: dict[str, float], verify_key: str, ocsp_prefix: str, assertion_prefix: str) -> float:
    return (
        stage_value_ms(stages, verify_key)
        + stage_value_ms(stages, f"{ocsp_prefix}OcspHttpQuery")
        + assertion_step_ms(stages, assertion_prefix)
    )


def pki_primary_stage_ms(row: pd.Series) -> float:
    stages = stage_map(row.get("stageTimingsJson", ""))
    assertion_prefix = "pkiLeafAssertion" if bool(row.get("crossBool", False)) else "pkiOpenSslAssertion"
    return cert_step_ms(stages, "pkiOpenSslVerifyLeaf", "pkiLeaf", assertion_prefix)


def stage_total_ms(row: pd.Series) -> float:
    stages = stage_map(row.get("stageTimingsJson", ""))
    return float(sum(float(value) for value in stages.values() if math.isfinite(float(value)) and float(value) > 0))


def finite_mean(values: list[float], fallback: float) -> float:
    clean = [float(value) for value in values if math.isfinite(float(value)) and float(value) > 0]
    return float(np.mean(clean)) if clean else float(fallback)


def pki_network_compensation_sec(completed: int, auth_count: int, ocsp_count: int) -> float:
    if completed <= 0:
        return 0.0
    total_ms = (auth_count * PKI_AUTH_NETWORK_SETUP_MS) + (ocsp_count * PKI_OCSP_NETWORK_RTT_MS)
    return total_ms / completed / 1000.0


def apply_pki_network_compensation(
    frame: pd.DataFrame,
    summary_path: Path,
    service_cas: int,
) -> pd.DataFrame:
    out = frame.copy()
    if not summary_path.exists() or "PKI_sim" not in out.columns:
        return out
    if "PKI_sim_raw" in out.columns and out["PKI_sim_raw"].notna().any():
        return out

    summary = pd.read_csv(summary_path)
    pki_summary = summary[summary["model"] == "PKI"].copy()
    if pki_summary.empty:
        return out

    for column in [
        "PKI_sim_raw",
        "pkiNetworkCompensationSec",
        "pkiNetworkCompensationMs",
        "pkiAuthNetworkSetupMs",
        "pkiOcspNetworkRttMs",
        "pkiAuthCount",
        "pkiOcspCount",
        "pkiCompleted",
    ]:
        if column not in out.columns:
            out[column] = math.nan

    for _, row in pki_summary.iterrows():
        epsilon = float(row["epsilon"])
        mask = out["PKI_sim"].notna() & np.isclose(out["epsilon"].astype(float), epsilon)
        if not mask.any():
            continue
        completed = int(row.get("completed", 0))
        management = int(row.get("managementCount", 0))
        cross = int(row.get("crossDomainCount", 0))
        auth_count = max(0, completed - management)
        ocsp_count = auth_count + PKI_CROSS_DOMAIN_CHAIN_STEPS * cross
        compensation = pki_network_compensation_sec(completed, auth_count, ocsp_count)
        raw = out.loc[mask, "PKI_sim"].astype(float)
        out.loc[mask, "PKI_sim_raw"] = raw
        out.loc[mask, "PKI_sim"] = raw + compensation
        out.loc[mask, "pkiNetworkCompensationSec"] = compensation
        out.loc[mask, "pkiNetworkCompensationMs"] = compensation * 1000.0
        out.loc[mask, "pkiAuthNetworkSetupMs"] = PKI_AUTH_NETWORK_SETUP_MS
        out.loc[mask, "pkiOcspNetworkRttMs"] = PKI_OCSP_NETWORK_RTT_MS
        out.loc[mask, "pkiAuthCount"] = auth_count
        out.loc[mask, "pkiOcspCount"] = ocsp_count
        out.loc[mask, "pkiCompleted"] = completed
        if "calibrationScope" in out.columns:
            out.loc[mask, "calibrationScope"] = "per-epsilon+local-ocsp-network-compensation"
    return out


def build_epsilon_summary(run_dir: Path) -> pd.DataFrame:
    detailed_path = run_dir / "real_simulation_results_by_epsilon_detailed.csv"
    summary_path = run_dir / "real_summary_by_epsilon_detailed.csv"
    calibration_path = run_dir / "real_calibrated_params.json"
    if not (detailed_path.exists() and summary_path.exists() and calibration_path.exists()):
        combined = pd.read_csv(run_dir / "combined_results_by_epsilon.csv").sort_values("epsilon")
        service_cas = BASE["service_cas"]
        if calibration_path.exists():
            calibration = json.loads(calibration_path.read_text(encoding="utf8"))
            service_cas = int(calibration.get("serviceCAs", service_cas))
        return apply_pki_network_compensation(combined, summary_path, service_cas).sort_values("epsilon")

    detailed = pd.read_csv(detailed_path)
    summary = pd.read_csv(summary_path)
    calibration = json.loads(calibration_path.read_text(encoding="utf8"))
    detailed["onChainBool"] = truthy(detailed["onChain"])
    detailed["crossBool"] = truthy(detailed["crossDomain"])

    lambda_block = float(calibration["lambdaBlockMeasured"])
    service_cas = int(calibration["serviceCAs"])
    fallback_mu = float(calibration["muModelOffchainAuthMeasured"])
    fallback_pki_mu = float(calibration["pkiMuPrimaryAuthMeasured"])
    fallback_pki_extra_mu = float(calibration.get("pkiMuCrossExtraCertificateMeasured") or fallback_pki_mu)
    fallback_pki_extra_sec = 1.0 / fallback_pki_extra_mu if fallback_pki_extra_mu > 0 else math.nan

    rows: list[dict[str, float]] = []
    for _, dpki_summary in summary[summary["model"] == "DPKI"].sort_values("epsilon").iterrows():
        epsilon = float(dpki_summary["epsilon"])
        dpki = detailed[(detailed["model"] == "DPKI") & (detailed["epsilon"].astype(float) == epsilon)].copy()
        pki = detailed[(detailed["model"] == "PKI") & (detailed["epsilon"].astype(float) == epsilon)].copy()
        pki_summary = summary[(summary["model"] == "PKI") & (summary["epsilon"].astype(float) == epsilon)]
        if dpki.empty or pki.empty or pki_summary.empty:
            continue

        arrival_span = float(dpki_summary.get("arrivalSpanSec", 0.0))
        lambda_total = len(dpki) / arrival_span if arrival_span > 0 else float(calibration["lambdaTotalMeasured"])
        p_manage = float((dpki["kind"] == "management").mean())
        normal_auth = dpki[dpki["kind"].isin(["intra-on-chain", "intra-off-chain"])]
        gamma = float((normal_auth["kind"] == "intra-on-chain").mean()) if len(normal_auth) else 0.0

        offchain_auth = dpki[dpki["kind"] == "intra-off-chain"]
        management = dpki[dpki["kind"] == "management"]
        mean_offchain_sec = finite_mean((offchain_auth["serviceMs"] / 1000.0).tolist(), 1.0 / fallback_mu)
        mean_management_sec = finite_mean((management["serviceMs"] / 1000.0).tolist(), float(calibration["meanManagementServiceSec"]))
        mu = 1.0 / mean_offchain_sec if mean_offchain_sec > 0 else fallback_mu
        q_manage = mean_offchain_sec / mean_management_sec if mean_management_sec > 0 else float(calibration["qManageMeasured"])

        pki_intra = pki[pki["kind"] == "intra-pki"]
        pki_mgmt = pki[pki["kind"] == "management"]
        pki_primary_sec = finite_mean((pki_intra["serviceMs"] / 1000.0).tolist(), float(calibration["pkiMeanPrimaryAuthServiceSec"]))
        pki_management_sec = finite_mean((pki_mgmt["serviceMs"] / 1000.0).tolist(), float(calibration["pkiMeanManagementServiceSec"]))
        pki_mu = 1.0 / pki_primary_sec if pki_primary_sec > 0 else fallback_pki_mu
        pki_q_manage = pki_primary_sec / pki_management_sec if pki_management_sec > 0 else float(calibration["pkiQManageMeasured"])

        cert_steps: list[float] = []
        for _, row in pki[pki["kind"] != "management"].iterrows():
            stages = stage_map(row.get("stageTimingsJson", ""))
            is_cross = bool(row.get("crossBool", False))
            leaf_assertion = "pkiLeafAssertion" if is_cross else "pkiOpenSslAssertion"
            cert_steps.append(cert_step_ms(stages, "pkiOpenSslVerifyLeaf", "pkiLeaf", leaf_assertion))
            if is_cross:
                cert_steps.append(cert_step_ms(stages, "pkiOpenSslVerifySourceCA", "pkiSourceCA", "pkiSourceCAAssertion"))
                cert_steps.append(cert_step_ms(stages, "pkiOpenSslVerifyRootCA", "pkiRootCA", "pkiRootCAAssertion"))
                cert_steps.append(cert_step_ms(stages, "pkiOpenSslVerifyTargetCA", "pkiTargetCA", "pkiTargetCAAssertion"))
        pki_extra_sec = pki_primary_sec
        pki_extra_mu = 1.0 / pki_extra_sec if pki_extra_sec > 0 else fallback_pki_extra_mu
        pki_row = pki_summary.iloc[0]
        existing_compensation = float(pki_row.get("pkiNetworkCompensationSec", math.nan))
        if math.isfinite(existing_compensation):
            pki_compensation = existing_compensation
            pki_sim_raw = float(pki_row.get("PKI_sim_raw", float(pki_row["E_T"]) - pki_compensation))
        else:
            pki_sim_raw = float(pki_row["E_T"])
            pki_compensation = math.nan
        pki_auth_count = int((pki["kind"] != "management").sum())
        pki_cross_count = int(pki["crossBool"].sum())
        pki_ocsp_count = pki_auth_count + PKI_CROSS_DOMAIN_CHAIN_STEPS * pki_cross_count
        if not math.isfinite(pki_compensation):
            pki_compensation = pki_network_compensation_sec(len(pki), pki_auth_count, pki_ocsp_count)

        params = ModelParams(
            lambda_total=lambda_total,
            p_manage=p_manage,
            q_manage=q_manage,
            mu=mu,
            service_cas=service_cas,
            gamma_on_chain=gamma,
            lambda_block=lambda_block,
            pki_mu=pki_mu,
            pki_q_manage=pki_q_manage,
            pki_cross_extra_mu=pki_extra_mu,
        )
        theory = theory_point(
            {
                "lambdaTotalMeasured": lambda_total,
                "pManageMeasured": p_manage,
                "qManageMeasured": q_manage,
                "muModelOffchainAuthMeasured": mu,
                "serviceCAs": service_cas,
                "gammaOnChainMeasured": gamma,
                "lambdaBlockMeasured": lambda_block,
                "pkiMuPrimaryAuthMeasured": pki_mu,
                "pkiQManageMeasured": pki_q_manage,
                "pkiMuCrossExtraCertificateMeasured": pki_extra_mu,
            },
            epsilon,
        )
        rows.append(
            {
                "epsilon": epsilon,
                "DPKI_sim": float(dpki_summary["E_T"]),
                "PKI_sim": pki_sim_raw + pki_compensation,
                "PKI_sim_raw": pki_sim_raw,
                "pkiNetworkCompensationSec": pki_compensation,
                "pkiNetworkCompensationMs": pki_compensation * 1000.0,
                "pkiAuthNetworkSetupMs": PKI_AUTH_NETWORK_SETUP_MS,
                "pkiOcspNetworkRttMs": PKI_OCSP_NETWORK_RTT_MS,
                "pkiAuthCount": pki_auth_count,
                "pkiOcspCount": pki_ocsp_count,
                "pkiCompleted": len(pki),
                **theory,
                "lambdaTotalMeasured": lambda_total,
                "pManageMeasured": p_manage,
                "gammaOnChainMeasured": gamma,
                "qManageMeasured": q_manage,
                "muModelOffchainAuthMeasured": mu,
                "lambdaBlockMeasured": lambda_block,
                "serviceCAs": service_cas,
                "pkiMuPrimaryAuthMeasured": pki_mu,
                "pkiQManageMeasured": pki_q_manage,
                "pkiMuCrossExtraCertificateMeasured": pki_extra_mu,
                "calibrationScope": "per-epsilon+local-ocsp-network-compensation",
            }
        )

    return pd.DataFrame(rows).sort_values("epsilon")


def plot_frame(
    df: pd.DataFrame,
    x_name: str,
    x_label: str,
    stem: str,
    title: str | None = None,
    y_limits: tuple[float, float] | None = None,
    include_pki: bool = True,
) -> None:
    out_dirs = [SCRIPT_DIR, REAL_OUT, SWEEP_ROOT]
    for out_dir in out_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    upper_df = df.dropna(subset=[x_name, "DPKI_upper_theory"])
    lower_df = df.dropna(subset=[x_name, "DPKI_lower_theory"])
    dpki_sim_df = df.dropna(subset=[x_name, "DPKI_sim"])
    pki_theory_df = df.dropna(subset=[x_name, "PKI_theory"]) if "PKI_theory" in df else pd.DataFrame()
    pki_sim_df = df.dropna(subset=[x_name, "PKI_sim"]) if "PKI_sim" in df else pd.DataFrame()

    ax.plot(
        upper_df[x_name],
        upper_df["DPKI_upper_theory"],
        "--",
        color=(0.0, 0.5, 0.0),
        linewidth=1.5,
        label="DPKI Upper Bound",
    )
    ax.plot(
        lower_df[x_name],
        lower_df["DPKI_lower_theory"],
        "--",
        color=(0.0, 0.447, 0.741),
        linewidth=1.5,
        label="DPKI Lower Bound",
    )
    ax.plot(
        dpki_sim_df[x_name],
        dpki_sim_df["DPKI_sim"],
        "-o",
        color=(1.0, 0.4, 0.0),
        linewidth=1.5,
        markersize=4,
        label="DPKI Experimental",
    )
    if include_pki and not pki_theory_df.empty:
        ax.plot(
            pki_theory_df[x_name],
            pki_theory_df["PKI_theory"],
            "-",
            color=(0.85, 0.0, 0.0),
            linewidth=1.2,
            alpha=0.75,
            label="_nolegend_",
        )
    if include_pki and not pki_sim_df.empty:
        ax.plot(
            pki_sim_df[x_name],
            pki_sim_df["PKI_sim"],
            "-o",
            color=(0.85, 0.0, 0.0),
            linewidth=1.5,
            markersize=4,
            label="PKI Analytical/Experimental",
        )
    ax.set_xlabel(x_label)
    ax.set_ylabel(r"$E[T]$")
    if title:
        ax.set_title(title)
    if y_limits:
        ax.set_ylim(*y_limits)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend(loc="best", fontsize=8, frameon=True)
    fig.tight_layout()
    for out_dir in out_dirs:
        df.to_csv(out_dir / f"{stem}.csv", index=False)
        fig.savefig(out_dir / f"{stem}.png", dpi=300)
        fig.savefig(out_dir / f"{stem}.eps", format="eps")
    plt.close(fig)


def epsilon_points() -> str:
    return ",".join(f"{x:.2f}".rstrip("0").rstrip(".") for x in np.arange(0, 0.6001, 0.05))


def epsilon_run_dirs() -> list[Path]:
    epsilon_root = SWEEP_ROOT / "epsilon"
    base = epsilon_root / "epsilon_lambdap30"
    extras = sorted(epsilon_root.glob("epsilon_lambdap30_extra*"))
    return [run_dir for run_dir in [base, *extras] if (run_dir / "combined_results_by_epsilon.csv").exists()]


def build_combined_epsilon_summary(run_dirs: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source_index, run_dir in enumerate(run_dirs):
        frame = build_epsilon_summary(run_dir).copy()
        if frame.empty:
            continue
        frame["sourceRun"] = run_dir.name
        frame["_sourceIndex"] = source_index
        frame["_hasSimulation"] = frame[["DPKI_sim", "PKI_sim"]].notna().any(axis=1).astype(int)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined = combined.sort_values(["epsilon", "_hasSimulation", "_sourceIndex"])
    combined = combined.drop_duplicates(subset=["epsilon"], keep="last")
    return combined.drop(columns=["_sourceIndex", "_hasSimulation"]).sort_values("epsilon")


def make_specs(args: argparse.Namespace) -> list[RunSpec]:
    specs: list[RunSpec] = []
    selected = set(args.only)
    if "epsilon" in selected:
        specs.append(
            RunSpec(
                label="epsilon_lambdap30",
                sweep="epsilon",
                x_name="epsilon",
                x_value=0.0,
                epsilon_points=epsilon_points(),
                requests=args.requests_epsilon,
                service_cas=BASE["service_cas"],
                service_shape_mode=args.service_shape_mode,
                seed=args.seed,
            )
        )
    if "lambda" in selected:
        for index, value in enumerate(args.lambda_values):
            specs.append(
                RunSpec(
                    label=f"lambda_{fmt_value(value)}",
                    sweep="lambda",
                    x_name="lambda",
                    x_value=value,
                    epsilon_points=str(BASE["epsilon"]),
                    requests=args.requests_sweep,
                    lambda_arrival=value,
                    service_shape_mode=args.service_shape_mode,
                    seed=args.seed + 1000 + index,
                    skip_pki=True,
                )
            )
    if "p" in selected:
        for index, value in enumerate(args.p_values):
            specs.append(
                RunSpec(
                    label=f"p_{fmt_value(value)}",
                    sweep="p",
                    x_name="p",
                    x_value=value,
                    epsilon_points=str(BASE["epsilon"]),
                    requests=args.requests_sweep,
                    p_manage=value,
                    service_shape_mode=args.service_shape_mode,
                    seed=args.seed + 2000 + index,
                )
            )
    if "M" in selected:
        for index, value in enumerate(args.m_values):
            specs.append(
                RunSpec(
                    label=f"M_{fmt_value(value)}",
                    sweep="M",
                    x_name="M",
                    x_value=value,
                    epsilon_points=str(BASE["epsilon"]),
                    requests=args.requests_sweep,
                    lambda_arrival=args.m_lambda_arrival,
                    service_cas=int(value),
                    service_shape_mode=args.service_shape_mode,
                    seed=args.seed + 3000,
                )
            )
    return specs


def parse_float_list(text: str) -> list[float]:
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and plot real DPKI/PKI sweeps with measured theory calibration.")
    parser.add_argument("--skip-run", action="store_true", help="Only rebuild plots from archived run outputs.")
    parser.add_argument("--requests-epsilon", type=int, default=1000)
    parser.add_argument("--requests-sweep", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=44000)
    parser.add_argument("--lambda-values", type=parse_float_list, default=parse_float_list("1,2,3,4,5"))
    parser.add_argument("--p-values", type=parse_float_list, default=parse_float_list("0,0.05,0.1,0.15,0.2,0.25,0.3"))
    parser.add_argument("--m-values", type=parse_float_list, default=parse_float_list("2,3,4,5,6,7,8"))
    parser.add_argument("--m-lambda-arrival", type=float, default=BASE["lambda_arrival"])
    parser.add_argument("--service-shape-mode", default=BASE["service_shape_mode"])
    parser.add_argument(
        "--only",
        choices=["epsilon", "lambda", "p", "M"],
        nargs="+",
        default=["epsilon", "lambda", "p", "M"],
        help="Limit which real sweeps are run and plotted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    SWEEP_ROOT.mkdir(parents=True, exist_ok=True)
    specs = make_specs(args)

    if not args.skip_run:
        for number, spec in enumerate(specs, start=1):
            print(f"[{number}/{len(specs)}] running {spec.sweep}:{spec.label}", flush=True)
            run_real_experiment(spec)

    selected = set(args.only)
    run_dirs = epsilon_run_dirs()
    if "epsilon" in selected and run_dirs:
        eps_df = build_combined_epsilon_summary(run_dirs)
        plot_frame(
            eps_df,
            "epsilon",
            r"$\epsilon$",
            "Fig7_epsilon_ET",
            y_limits=(0.05, 0.18),
            include_pki=True,
        )
        plot_frame(
            eps_df,
            "epsilon",
            r"$\epsilon$",
            "Fig7_epsilon_ET_lambdap30_y005_020",
            y_limits=(0.05, 0.18),
            include_pki=True,
        )

    for sweep, x_name, x_label, stem in [
        ("lambda", "lambda", r"$\lambda$", "Fig_lambda_ET"),
        ("p", "p", r"$p$", "Fig_p_ET"),
        ("M", "M", r"$M$", "Fig_M_ET"),
    ]:
        rows = []
        for spec in [item for item in specs if item.sweep == sweep]:
            run_dir = SWEEP_ROOT / sweep / spec.label
            if run_dir.exists():
                rows.append(read_run_point(run_dir, x_name, spec.x_value, BASE["epsilon"]))
        if rows:
            df = pd.DataFrame(rows).sort_values(x_name)
            plot_frame(df, x_name, x_label, stem, include_pki=(sweep != "lambda"))

    print(f"wrote figures and CSVs under {SCRIPT_DIR}, {REAL_OUT}, and {SWEEP_ROOT}", flush=True)


if __name__ == "__main__":
    main()
