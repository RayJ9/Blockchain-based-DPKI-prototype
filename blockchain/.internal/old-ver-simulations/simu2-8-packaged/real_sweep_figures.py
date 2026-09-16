"""Run and archive unmodified prototype measurements for public sweeps."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = WORKSPACE_ROOT / "blockchain" / "dpki-experiment"
RUN_REAL = EXPERIMENT_DIR / "run-real-dpki-experiment.js"
REAL_OUT = EXPERIMENT_DIR / "outputs"
POW_RUNTIME = Path(os.environ.get("DPKI_CHAIN_RUNTIME", str(WORKSPACE_ROOT / "blockchain/pow-4nodes-runtime/runtime"))).resolve()
SWEEP_ROOT = REAL_OUT / "real_sweeps"

@dataclass(frozen=True)
class RunSpec:
    label: str
    sweep: str
    x_name: str
    x_value: float
    epsilon_points: str
    requests: int
    lambda_arrival: float = 3.0
    p_manage: float = 0.1
    gamma_on_chain: float = 0.1
    q_manage: float = 0.3
    service_cas: int = 4
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
    lambda_block: float = 30.0
    arrival_mode: str = "wall"
    kind_plan_mode: str = "fixed"
    dpki_root_read_mode: str = "chain"
    dpki_proof_read_mode: str = "http"
    dpki_proof_base_port: int = 20080
    actual_execution_mode: str = "parallel"
    pki_service_base_port: int = 21080
    seed: int = 44000
    skip_pki: bool = False


def fmt_value(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value).replace(".", "p").replace("-", "m")


def run_real_experiment(spec: RunSpec) -> Path:
    if spec.arrival_mode != "wall":
        raise ValueError("Prototype measurements require wall-clock arrivals")
    dest = SWEEP_ROOT / spec.sweep / spec.label
    dest.mkdir(parents=True, exist_ok=True)
    cmd = ["node", str(RUN_REAL), "--consensus-backend", "pow",
           "--rpc", os.environ.get("DPKI_EXPERIMENT_RPC", "http://127.0.0.1:8545"),
           "--pow-rpc", os.environ.get("DPKI_EXPERIMENT_JRPC", "http://127.0.0.1:8801"),
           "--pow-runtime", str(POW_RUNTIME), "--pow-warmup-ms", "10000"]
    names = {"requests": "requests-per-epsilon"}
    excluded = {"label", "sweep", "x_name", "x_value", "estimate_gas", "skip_pki", "chain_id"}
    for name, value in spec.__dict__.items():
        if name in excluded or value is None:
            continue
        cmd.extend(["--" + names.get(name, name.replace("_", "-")), str(value)])
    chain_id = spec.chain_id or int(os.environ.get("DPKI_CHAIN_ID", "0"))
    if chain_id:
        cmd.extend(["--chain-id", str(chain_id)])
    if spec.estimate_gas:
        cmd.append("--estimate-gas")
    if spec.skip_pki:
        cmd.append("--skip-pki")
    (dest / "run_config.json").write_text(json.dumps({
        "cmd": cmd, "spec": spec.__dict__, "measurementMode": "unmodified wall-clock request timings",
        "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, indent=2), encoding="utf8")
    with (dest / "run.log").open("w", encoding="utf8") as log:
        log.write(" ".join(cmd) + "\n\n")
        log.flush()
        child = subprocess.Popen(cmd, cwd=EXPERIMENT_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf8", errors="replace", bufsize=1)
        assert child.stdout is not None
        for line in child.stdout:
            log.write(line)
            log.flush()
            if os.environ.get("DPKI_LIVE_TRACE", "").lower() in {"1", "true", "yes", "on"}:
                print(line, end="", flush=True)
        return_code = child.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)
    archive_outputs(dest)
    return dest


def archive_outputs(dest: Path) -> None:
    for name in ["measured_parameters.json", "real_simulation_results_by_epsilon.csv",
                 "real_simulation_results_by_epsilon_detailed.csv", "real_summary_by_epsilon_detailed.csv",
                 "real_stage_statistics.csv", "real_chain_observation.json", "real_chain_tx_breakdown.csv"]:
        source = REAL_OUT / name
        if source.exists():
            shutil.copy2(source, dest / name)
