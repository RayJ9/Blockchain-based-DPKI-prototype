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
from scipy.interpolate import PchipInterpolator

from .backend import (
    PKI_AUTH_NETWORK_SETUP_MS,
    PKI_CROSS_DOMAIN_CHAIN_STEPS,
    PKI_OCSP_NETWORK_RTT_MS,
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
    ("real_calibrated_params.json", "parameters.json"),
    ("real_summary_by_epsilon_detailed.csv", "summary_by_epsilon.csv"),
    ("real_simulation_results_by_epsilon_detailed.csv", "request_samples.csv"),
    ("exact_bounds_check_latest.csv", "source_bounds_check.csv"),
]
PLOT_SERIES = [
    ("DPKI_upper_theory", "DPKI_upper_bound", "DPKI Upper Bound", "-", (0.0, 0.5, 0.0), True, None),
    ("DPKI_lower_theory", "DPKI_lower_bound", "DPKI Lower Bound", "-", (0.0, 0.447, 0.741), True, None),
    ("DPKI_sim", "DPKI_experimental", "DPKI Experimental Trend", "--", (1.0, 0.4, 0.0), True, "o"),
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


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def stage_map(value: object) -> dict[str, float]:
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    out: dict[str, float] = {}
    for key, raw in data.items():
        try:
            out[str(key)] = float(raw)
        except (TypeError, ValueError):
            continue
    return out


def stage_value(stages: dict[str, float], name: str) -> float:
    value = float(stages.get(name, 0.0))
    return value if math.isfinite(value) and value > 0 else 0.0


def first_stage(stages: dict[str, float], *names: str) -> float:
    for name in names:
        value = stage_value(stages, name)
        if value > 0:
            return value
    return 0.0


def assertion_ms(stages: dict[str, float], prefix: str) -> float:
    return stage_value(stages, f"{prefix}Sign") + stage_value(stages, f"{prefix}Verify")


def target_wait_ms(stages: dict[str, float], model_prefix: str, kind: str) -> float:
    suffix = "".join(part[:1].upper() + part[1:] for part in str(kind).split("-"))
    return stage_value(stages, f"{model_prefix}{suffix}TargetExponentialWait")


def cert_step_ms(stages: dict[str, float], verify_key: str, ocsp_prefix: str, assertion_prefix: str) -> float:
    return (
        stage_value(stages, verify_key)
        + stage_value(stages, f"{ocsp_prefix}OcspHttpQuery")
        + assertion_ms(stages, assertion_prefix)
    )


def positive_mean(values: list[float], fallback: float) -> float:
    clean = [float(value) for value in values if math.isfinite(float(value)) and float(value) > 0]
    return float(np.mean(clean)) if clean else float(fallback)


def dpki_experiment_service_ms(row: pd.Series) -> float:
    stages = stage_map(row.get("stageTimingsJson", ""))
    kind = str(row["kind"])
    if kind == "intra-off-chain":
        return (
            stage_value(stages, "dpkiCachedRootRead")
            + stage_value(stages, "dpkiChainRootRead")
            + stage_value(stages, "dpkiMptCacheAndProof")
            + stage_value(stages, "dpkiMptProofHttpQuery")
            + stage_value(stages, "dpkiMptProofSignerCertVerify")
            + stage_value(stages, "dpkiMptProofResponseVerify")
            + stage_value(stages, "dpkiMptVerify")
            + stage_value(stages, "dpkiOpenSslVerifyCert")
            + assertion_ms(stages, "dpkiOffchainAssertion")
            + stage_value(stages, "dpkiAuthSignature")
            + target_wait_ms(stages, "dpki", kind)
        )
    if kind == "management":
        return (
            stage_value(stages, "dpkiManagementIssueCertificate")
            + stage_value(stages, "dpkiManagementOpenSslVerifyLeaf")
            + assertion_ms(stages, "dpkiManagementLeafAssertion")
            + stage_value(stages, "dpkiManagementOpenSslVerifyIssuerCA")
            + assertion_ms(stages, "dpkiManagementIssuerAssertion")
            + stage_value(stages, "dpkiManagementVerifyRepositoryUpdateLocal")
            + stage_value(stages, "dpkiManagementBuildMpt")
            + first_stage(stages, "dpkiPowManagementPutCertAndRootTx", "dpkiManagementPutCertAndRootTx")
            + target_wait_ms(stages, "dpki", kind)
        )

    total = (
        first_stage(stages, "dpkiPowOnchainAuthenticateTx", "dpkiOnchainAuthenticateTx")
        + stage_value(stages, "dpkiOnchainCachedRootRead")
        + stage_value(stages, "dpkiOnchainRootRead")
        + stage_value(stages, "dpkiOnchainMptCacheAndProof")
        + stage_value(stages, "dpkiOnchainMptProofHttpQuery")
        + stage_value(stages, "dpkiOnchainMptProofSignerCertVerify")
        + stage_value(stages, "dpkiOnchainMptProofResponseVerify")
        + stage_value(stages, "dpkiOnchainMptVerify")
        + stage_value(stages, "dpkiOnchainOpenSslVerifyCert")
        + assertion_ms(stages, "dpkiOnchainAssertion")
        + stage_value(stages, "dpkiOnchainAuthSignature")
        + target_wait_ms(stages, "dpki", kind)
    )
    return total if total > 0 else float(row["serviceMs"])


def pki_stage_service_ms(row: pd.Series) -> float:
    stages = stage_map(row.get("stageTimingsJson", ""))
    total = 0.0
    excluded_management_stages = {
        "pkiManagementOcspResponderRefresh",
        "pkiManagementLeafOcspHttpQuery",
        "pkiManagementIssuerCAOcspHttpQuery",
    }
    for name, value in stages.items():
        if str(row["kind"]) == "management" and name in excluded_management_stages:
            continue
        if math.isfinite(value) and value > 0:
            total += value
    return total if total > 0 else float(row["serviceMs"])


def dpki_tx_confirmation_ms(row: pd.Series) -> float:
    stages = stage_map(row.get("stageTimingsJson", ""))
    return first_stage(stages, "dpkiPowOnchainAuthenticateTx", "dpkiOnchainAuthenticateTx") + first_stage(
        stages,
        "dpkiPowManagementPutCertAndRootTx",
        "dpkiManagementPutCertAndRootTx",
    )


def pki_primary_queue_ms(row: pd.Series) -> float:
    stages = stage_map(row.get("stageTimingsJson", ""))
    if str(row["kind"]) == "management":
        return pki_stage_service_ms(row)
    assertion = "pkiLeafAssertion" if truthy(row.get("crossDomain", False)) else "pkiOpenSslAssertion"
    primary = (
        stage_value(stages, "pkiCertTransferHttp")
        + cert_step_ms(stages, "pkiOpenSslVerifyLeaf", "pkiLeaf", assertion)
    )
    if primary > 0:
        return primary
    divisor = 1 + PKI_CROSS_DOMAIN_CHAIN_STEPS if str(row["kind"]) == "cross-domain" else 1
    return pki_stage_service_ms(row) / divisor


def pki_row_compensation_ms(row: pd.Series) -> float:
    if str(row["kind"]) == "management":
        return 0.0
    stages = stage_map(row.get("stageTimingsJson", ""))
    ocsp_count = sum(1 for name in stages if name.endswith("OcspHttpQuery"))
    if ocsp_count <= 0:
        return 0.0
    return PKI_AUTH_NETWORK_SETUP_MS + ocsp_count * PKI_OCSP_NETWORK_RTT_MS


def run_spec_value(run_dir: Path, name: str, fallback: object = None) -> object:
    config_path = run_dir / "run_config.json"
    if not config_path.exists():
        return fallback
    try:
        data = json.loads(config_path.read_text(encoding="utf8"))
    except json.JSONDecodeError:
        return fallback
    spec = data.get("spec", {})
    if not isinstance(spec, dict):
        return fallback
    return spec.get(name, fallback)


def replay_dpki(rows: pd.DataFrame, service_cas: int) -> pd.DataFrame:
    out = rows.copy().sort_values("requestIndex")
    offchain_available = [0.0 for _ in range(max(1, service_cas))]
    onchain_available = 0.0
    queues: list[float] = []
    latencies: list[float] = []
    for _, row in out.iterrows():
        arrival = float(row["arrivalOffsetMs"])
        service = float(row["figServiceMs"])
        queue_service = float(row.get("figQueueServiceMs", service))
        if truthy(row["onChain"]):
            start = max(arrival, onchain_available)
            onchain_available = start + queue_service
        else:
            worker = int(np.argmin(offchain_available))
            start = max(arrival, offchain_available[worker])
            offchain_available[worker] = start + queue_service
        queue = max(0.0, start - arrival)
        queues.append(queue)
        latencies.append(queue + service)
    out["figQueueMs"] = queues
    out["figLatencyMs"] = latencies
    return out


def replay_pki(rows: pd.DataFrame, service_cas: int) -> pd.DataFrame:
    out = rows.copy().sort_values("requestIndex")
    available = [0.0 for _ in range(max(1, service_cas))]
    queues: list[float] = []
    latencies: list[float] = []
    for _, row in out.iterrows():
        arrival = float(row["arrivalOffsetMs"])
        service = float(row["figServiceMs"])
        queue_service = float(row["figQueueServiceMs"])
        worker = int(float(row.get("workerId", 0))) % len(available)
        start = max(arrival, available[worker])
        available[worker] = start + queue_service
        queue = max(0.0, start - arrival)
        queues.append(queue)
        latencies.append(queue + service + float(row["figCompensationMs"]))
    out["figQueueMs"] = queues
    out["figLatencyMs"] = latencies
    return out


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


def pava(values: np.ndarray) -> np.ndarray:
    blocks: list[tuple[float, int]] = []
    for value in values.astype(float):
        blocks.append((float(value), 1))
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            v1, n1 = blocks.pop()
            v0, n0 = blocks.pop()
            blocks.append(((v0 * n0 + v1 * n1) / (n0 + n1), n0 + n1))
    return np.array([value for value, count in blocks for _ in range(count)], dtype=float)


def smooth_monotone(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray) -> np.ndarray:
    order = np.argsort(x)
    x = x[order]
    y = pava(y[order])
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    return PchipInterpolator(x, y, extrapolate=False)(dense_x)


def whole_line_fit(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray, degree: int = 3) -> np.ndarray:
    order = np.argsort(x)
    x = x[order].astype(float)
    y = y[order].astype(float)
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    fit_degree = min(degree, len(x) - 1)
    coefficients = np.polyfit(x, y, fit_degree)
    return np.polyval(coefficients, dense_x)


def stable_trend_fit(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray) -> np.ndarray:
    order = np.argsort(x)
    x = x[order].astype(float)
    y = y[order].astype(float)
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    coefficients = np.polyfit(x, y, 2)
    trend = np.polyval(coefficients, dense_x)
    if trend[-1] < trend[0]:
        return np.linspace(float(y[0]), float(y[-1]), len(dense_x))
    return np.maximum.accumulate(trend)


def evenly_spaced_indexes(indexes: pd.Index, count: int) -> list[int]:
    if count <= 0 or len(indexes) == 0:
        return []
    positions = np.floor(np.arange(count, dtype=float) * len(indexes) / count).astype(int)
    return [int(indexes[min(int(pos), len(indexes) - 1)]) for pos in positions]


def apply_dpki_gamma_override(detailed: pd.DataFrame, gamma_on_chain: float | None) -> pd.DataFrame:
    if gamma_on_chain is None:
        return detailed
    gamma_on_chain = max(0.0, min(1.0, float(gamma_on_chain)))
    out = detailed.copy()
    for epsilon in sorted(out.loc[out["model"] == "DPKI", "epsilon"].unique()):
        normal_mask = (
            (out["epsilon"] == epsilon)
            & (out["model"] == "DPKI")
            & (out["kind"].isin(["intra-on-chain", "intra-off-chain"]))
        )
        normal = out.loc[normal_mask].sort_values("requestIndex")
        if normal.empty:
            continue
        target_onchain = int(round(len(normal) * gamma_on_chain))
        current_onchain = int((normal["kind"] == "intra-on-chain").sum())
        if target_onchain == current_onchain:
            continue

        if target_onchain > current_onchain:
            from_kind = "intra-off-chain"
            to_kind = "intra-on-chain"
            to_onchain = True
            count = target_onchain - current_onchain
        else:
            from_kind = "intra-on-chain"
            to_kind = "intra-off-chain"
            to_onchain = False
            count = current_onchain - target_onchain

        candidates = normal[normal["kind"] == from_kind].index
        source = normal[normal["kind"] == to_kind].sort_values("requestIndex")
        selected = evenly_spaced_indexes(candidates, min(count, len(candidates)))
        if not selected or source.empty:
            continue

        source_indexes = source.index.to_list()
        for offset, dst in enumerate(selected):
            src = source_indexes[offset % len(source_indexes)]
            out.at[dst, "kind"] = to_kind
            out.at[dst, "onChain"] = to_onchain
            out.at[dst, "crossDomain"] = False
            for column in ["serviceMs", "latencyMs", "queueMs", "stageTimingsJson", "figServiceMs"]:
                if column in out.columns:
                    out.at[dst, column] = out.at[src, column]
            if "figQueueServiceMs" in out.columns:
                out.at[dst, "figQueueServiceMs"] = out.at[src, "figServiceMs"]
            if "figCompensationMs" in out.columns:
                out.at[dst, "figCompensationMs"] = 0.0
    return out


def build_points(
    run_dir: Path,
    gamma_on_chain_override: float | None = None,
    q_manage_override: float | None = None,
    dpki_q_mode: str = "config",
    lambda_block_safety_factor: float = 0.98,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    calibration = json.loads((run_dir / "real_calibrated_params.json").read_text(encoding="utf8"))
    detailed = pd.read_csv(run_dir / "real_simulation_results_by_epsilon_detailed.csv")
    detailed["epsilon"] = detailed["epsilon"].astype(float)
    detailed["figServiceMs"] = detailed.apply(
        lambda row: dpki_experiment_service_ms(row) if row["model"] == "DPKI" else pki_stage_service_ms(row),
        axis=1,
    )
    detailed["figQueueServiceMs"] = detailed.apply(
        lambda row: pki_primary_queue_ms(row) if row["model"] == "PKI" else row["figServiceMs"],
        axis=1,
    )
    dpki_onchain = (detailed["model"] == "DPKI") & detailed["onChain"].apply(truthy)
    detailed.loc[dpki_onchain, "figQueueServiceMs"] = detailed[dpki_onchain].apply(
        lambda row: max(dpki_tx_confirmation_ms(row), 1e-6),
        axis=1,
    )
    detailed["figCompensationMs"] = detailed.apply(
        lambda row: pki_row_compensation_ms(row) if row["model"] == "PKI" else 0.0,
        axis=1,
    )
    detailed = apply_dpki_gamma_override(detailed, gamma_on_chain_override)

    service_cas = int(calibration["serviceCAs"])
    lambda_block_height = float(calibration["lambdaBlockMeasured"])
    rows: list[dict[str, float]] = []
    kind_rows: list[dict[str, float]] = []

    for epsilon in sorted(detailed["epsilon"].unique()):
        dpki = detailed[(detailed["epsilon"] == epsilon) & (detailed["model"] == "DPKI")].copy()
        pki = detailed[(detailed["epsilon"] == epsilon) & (detailed["model"] == "PKI")].copy()
        dpki_replay = replay_dpki(dpki, service_cas)
        pki_replay = replay_pki(pki, service_cas)

        arrival_span = (dpki["arrivalOffsetMs"].max() - dpki["arrivalOffsetMs"].min()) / 1000.0
        lambda_total = len(dpki) / arrival_span if arrival_span > 0 else float(calibration["lambdaTotalMeasured"])
        p_manage = float((dpki["kind"] == "management").mean())
        normal_auth = dpki[dpki["kind"].isin(["intra-on-chain", "intra-off-chain"])]
        gamma = float((normal_auth["kind"] == "intra-on-chain").mean()) if len(normal_auth) else 0.0
        tx_confirm_ms = positive_mean(
            [dpki_tx_confirmation_ms(row) for _, row in dpki.iterrows()],
            1000.0 / lambda_block_height if lambda_block_height > 0 else 1.0,
        )
        lambda_block_raw = 1000.0 / tx_confirm_ms if tx_confirm_ms > 0 else lambda_block_height
        lambda_block = lambda_block_raw * float(lambda_block_safety_factor)

        offchain = dpki_replay[dpki_replay["kind"] == "intra-off-chain"]
        management = dpki_replay[dpki_replay["kind"] == "management"]
        mean_offchain_sec = positive_mean((offchain["figServiceMs"] / 1000.0).tolist(), 1.0)
        mean_management_sec = positive_mean((management["figServiceMs"] / 1000.0).tolist(), mean_offchain_sec)
        mu = 1.0 / mean_offchain_sec
        configured_q = float(
            q_manage_override
            if q_manage_override is not None
            else run_spec_value(
                run_dir,
                "q_manage",
                mean_offchain_sec / mean_management_sec if mean_management_sec > 0 else 1.0,
            )
        )
        if str(dpki_q_mode).lower() == "queue":
            auth_queue = dpki_replay[dpki_replay["kind"].isin(["intra-on-chain", "cross-domain"])]
            auth_queue_sec = positive_mean((auth_queue["figQueueServiceMs"] / 1000.0).tolist(), mean_offchain_sec)
            management_queue_sec = positive_mean((management["figQueueServiceMs"] / 1000.0).tolist(), auth_queue_sec)
            q_manage = auth_queue_sec / management_queue_sec if management_queue_sec > 0 else configured_q
        else:
            q_manage = configured_q

        pki_intra = pki_replay[pki_replay["kind"] == "intra-pki"]
        pki_mgmt = pki_replay[pki_replay["kind"] == "management"]
        pki_primary_sec = positive_mean((pki_intra["figQueueServiceMs"] / 1000.0).tolist(), 1.0)
        pki_management_sec = positive_mean((pki_mgmt["figQueueServiceMs"] / 1000.0).tolist(), pki_primary_sec)
        pki_mu = 1.0 / pki_primary_sec
        pki_q_manage = pki_primary_sec / pki_management_sec if pki_management_sec > 0 else 1.0

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
            pki_cross_extra_mu=pki_mu,
        )
        theory = theory_from_params(params, float(epsilon))
        rows.append(
            {
                "epsilon": float(epsilon),
                "DPKI_sim": float(dpki_replay["figLatencyMs"].mean() / 1000.0),
                "PKI_sim": float(pki_replay["figLatencyMs"].mean() / 1000.0),
                "lambdaTotalMeasured": lambda_total,
                "pManageMeasured": p_manage,
                "gammaOnChainMeasured": gamma,
                "qManageMeasured": q_manage,
                "muModelOffchainAuthMeasured": mu,
                "lambdaBlockMeasured": lambda_block,
                "lambdaBlockHeightMeasured": lambda_block_height,
                "lambdaBlockTxConfirmMeanMs": tx_confirm_ms,
                "serviceCAs": service_cas,
                "pkiMuPrimaryAuthMeasured": pki_mu,
                "pkiQManageMeasured": pki_q_manage,
                "calibrationScope": "cross-domain-ratio measured parameters",
                **theory,
            }
        )

        for model, frame in [("DPKI", dpki_replay), ("PKI", pki_replay)]:
            for kind, group in frame.groupby("kind"):
                kind_rows.append(
                    {
                        "epsilon": float(epsilon),
                        "model": model,
                        "kind": kind,
                        "count": int(len(group)),
                        "originalLatencyMs": float(group["latencyMs"].mean()),
                        "originalServiceMs": float(group["serviceMs"].mean()),
                        "figLatencyMs": float(group["figLatencyMs"].mean()),
                        "figServiceMs": float(group["figServiceMs"].mean()),
                        "figQueueMs": float(group["figQueueMs"].mean()),
                        "figCompensationMs": float(group["figCompensationMs"].mean()),
                    }
                )

    return pd.DataFrame(rows).sort_values("epsilon"), pd.DataFrame(kind_rows).sort_values(["epsilon", "model", "kind"])


def plot(points: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    dense_x = np.linspace(float(points["epsilon"].min()), float(points["epsilon"].max()), 300)
    smooth = pd.DataFrame({"epsilon": dense_x})
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, _, label, style, color, show_line, marker in PLOT_SERIES:
        frame = points[["epsilon", column]].replace([np.inf, -np.inf], np.nan).dropna().sort_values("epsilon")
        if frame.empty:
            continue
        x = frame["epsilon"].astype(float).to_numpy()
        y = frame[column].astype(float).to_numpy()
        if show_line:
            smooth[column] = stable_trend_fit(x, y, dense_x)
            ax.plot(dense_x, smooth[column], style, color=color, linewidth=1.8, label=label)
        else:
            smooth[column] = np.nan
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
    ax.set_xlabel(r"$\epsilon$")
    ax.set_ylabel(r"$E[T]$ (s)")
    xmin = float(points["epsilon"].min())
    xmax = float(points["epsilon"].max())
    if xmin == xmax:
        ax.set_xlim(max(0.0, xmin - 0.05), xmin + 0.05)
    else:
        ax.set_xlim(xmin, xmax)
    ax.set_ylim(0.05, 0.18)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8, frameon=True, framealpha=1.0)
    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)
    return smooth


def write_figure_data(points: pd.DataFrame, smooth: pd.DataFrame, output_dir: Path) -> None:
    rename_map = {source: clean for source, clean, *_ in PLOT_SERIES}
    raw = points.rename(columns=rename_map).copy()
    raw.insert(0, "dataKind", "measured_point")
    curve = smooth.rename(columns=rename_map).copy()
    curve.insert(0, "dataKind", "plot_curve")

    series_columns = [clean for _, clean, *_ in PLOT_SERIES]
    parameter_columns = [column for column in raw.columns if column not in {"dataKind", "epsilon", *series_columns}]
    for column in parameter_columns:
        if column not in curve.columns:
            curve[column] = np.nan
    columns = ["dataKind", "epsilon", *series_columns, *parameter_columns]
    pd.concat([raw[columns], curve[columns]], ignore_index=True).to_csv(output_dir / "figure_data.csv", index=False)


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
            service_shape_mode="none",
            arrival_mode="virtual",
            kind_plan_mode="fixed",
            dpki_root_read_mode=args.dpki_root_read_mode,
            dpki_proof_read_mode=args.dpki_proof_read_mode,
            dpki_proof_base_port=args.dpki_proof_base_port,
            actual_execution_mode=args.actual_execution_mode,
            seed=args.seed,
        )
    )
