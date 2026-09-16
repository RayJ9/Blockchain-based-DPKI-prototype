"""Run the paper's service-CA fault scenarios and aggregate raw request outcomes.

Examples (with the experiment chain already running):
  python -m figure_dpki_pki_runtime.availability_experiment --figure 9 --requests 50
  python -m figure_dpki_pki_runtime.availability_experiment --aggregate-only PATH

No theoretical bounds, fitted delays, or precomputed means enter this runner.
The publication does not specify a fault resampling interval: a fault mask is
held fixed for one round and independently sampled again for the next round.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def number_list(text: str, kind=float):
    values = [kind(token.strip()) for token in text.split(",") if token.strip()]
    if not values or len(set(values)) != len(values):
        raise ValueError("Parameter lists must be nonempty and contain unique values")
    return values


def aggregate(output_dir: Path) -> pd.DataFrame:
    manifest = json.loads((output_dir / "availability_manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete":
        raise ValueError("Incomplete/failed runs cannot be exported as availability measurements")
    config = manifest["config"]
    expected_groups = {(scenario, m, pf, model) for scenario in config["scenarios"]
                       for m in config["mValues"] for pf in config["pfValues"] for model in ("DPKI", "PKI")}
    expected_count = config["rounds"] * config["requestsPerRound"]
    requests_per_round = config["warmupRequests"] + config["requestsPerRound"]
    groups = defaultdict(lambda: {ts: {"success": 0, "inherent_failure": 0, "timeout": 0}
                                  for ts in config["timeoutsSec"]})
    seen = defaultdict(int)
    measurement_count = 0
    digest = hashlib.sha256()
    with (output_dir / "availability_requests.jsonl").open("rb") as handle:
        for line in handle:
            digest.update(line)
            record = json.loads(line)
            if record["runId"] != manifest["runId"]:
                raise ValueError("Mixed run identities")
            point = (record["scenario"], record["m"], record["pf"], record["model"])
            index, round_id = record["index"], record["round"]
            if (point not in expected_groups or not isinstance(index, int) or not 0 <= index < requests_per_round
                    or not isinstance(round_id, int) or not 0 <= round_id < config["rounds"]):
                raise ValueError("Unexpected request identity")
            key = (*point, round_id)
            bit = 1 << index
            if seen[key] & bit:
                raise ValueError("Duplicate request record")
            seen[key] |= bit
            latency = record["latencyMs"]
            if not math.isfinite(latency) or latency < 0 or not math.isclose(
                    latency, record["finishWallMs"] - record["arrivalWallMs"], abs_tol=1e-7):
                raise ValueError("Invalid raw wall-clock latency")
            if record["error"] or bool(record["completedSuccessfully"]) == bool(record["inherentFailure"]):
                raise ValueError("Unexpected or contradictory request outcome")
            phase = "warmup" if index < config["warmupRequests"] else "measurement"
            if record["phase"] != phase:
                raise ValueError("Request phase does not match its configured index")
            if phase == "measurement":
                measurement_count += 1
                for ts in config["timeoutsSec"]:
                    outcome = "inherent_failure" if record["inherentFailure"] else "timeout" if latency > ts * 1000 else "success"
                    groups[point][ts][outcome] += 1
    if digest.hexdigest() != manifest["requestLogSha256"]:
        raise ValueError("The request log differs from the completed run's recorded SHA-256")
    if set(groups) != expected_groups or measurement_count != manifest["measurementRecords"]:
        raise ValueError("Missing parameter points or request records")
    if len(seen) != len(expected_groups) * config["rounds"] or any(
            bits != (1 << requests_per_round) - 1 for bits in seen.values()):
        raise ValueError("Missing warmup or measurement requests")
    rows = []
    for (scenario, m, pf, model), thresholds in groups.items():
        for ts, counts in thresholds.items():
            inherent, timeout, success = counts["inherent_failure"], counts["timeout"], counts["success"]
            if inherent + timeout + success != expected_count:
                raise ValueError("Failure classes are not exhaustive and disjoint")
            rows.append({"scenario": scenario, "m": m, "pf": pf, "model": model, "timeoutSec": ts,
                         "requests": expected_count, "success": success, "inherent_failure": inherent,
                         "timeout": timeout, "availability": success / expected_count,
                         "Fi": inherent / expected_count, "Ft": timeout / expected_count})
    frame = pd.DataFrame(rows)
    # Independently check the live runner's counts before producing the wide table.
    live = pd.read_csv(output_dir / "availability_summary.csv", float_precision="round_trip")
    keys = ["scenario", "m", "pf", "model", "timeoutSec"]
    counts = ["requests", "success", "inherent_failure", "timeout"]
    left = frame.set_index(keys).sort_index()[counts]
    right = live.set_index(keys).sort_index()[counts]
    pd.testing.assert_frame_equal(left, right, check_dtype=False)
    wide = frame.pivot(index=["scenario", "m", "pf", "timeoutSec"], columns="model",
                       values=["availability", "Fi", "Ft", "requests"])
    wide.columns = [f"{model}_{'Mean' if field == 'availability' else field}" for field, model in wide.columns]
    wide = wide.reset_index().rename(columns={"timeoutSec": "ts"})
    wide["samplingMode"] = "fixed_mask_diagnostic" if "fixedFaultyCaIds" in config else "bernoulli_rounds"
    wide.to_csv(output_dir / "availability_measured.csv", index=False)
    return frame


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aggregate-only", type=Path)
    parser.add_argument("--figure", choices=[9, 10], type=int, default=9)
    parser.add_argument("--requests", type=int, default=50, help="Measured requests per model and independent fault round")
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--warmup-requests", type=int, default=20)
    parser.add_argument("--pf-values", default="0,0.2,0.6,1")
    parser.add_argument("--m-values", default="")
    parser.add_argument("--timeouts", default="")
    parser.add_argument("--scenario", choices=["both", "nonresponding", "malicious"], default="both")
    parser.add_argument("--seed", type=int, default=20260916)
    parser.add_argument("--fixed-faulty-ca-ids", help="Single-point diagnostic only; comma-separated zero-based CA ids")
    parser.add_argument("--lambda-arrival", type=float, default=6.0)
    parser.add_argument("--p-manage", type=float, default=0.1)
    parser.add_argument("--gamma-on-chain", type=float, default=0.1)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--rpc", default=os.environ.get("DPKI_EXPERIMENT_RPC", "http://127.0.0.1:8545"))
    parser.add_argument("--pow-rpc", default=os.environ.get("DPKI_EXPERIMENT_JRPC", "http://127.0.0.1:8801"))
    parser.add_argument("--pow-runtime", default=os.environ.get("DPKI_CHAIN_RUNTIME", str(ROOT / "blockchain/pow-4nodes-runtime/runtime")))
    parser.add_argument("--chain-id", default=os.environ.get("DPKI_CHAIN_ID", "0"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.lambda_arrival <= 0 or not math.isfinite(args.lambda_arrival):
        parser.error("--lambda-arrival must be finite and positive")
    if any(not 0 <= x <= 1 for x in [args.p_manage, args.gamma_on_chain, args.epsilon]):
        parser.error("Workload probabilities must lie in [0,1]")
    return args


def main():
    args = parse_args()
    if args.aggregate_only:
        aggregate(args.aggregate_only.resolve())
        return
    output = (args.output_dir or ROOT / "experiment_artifacts" / "availability" /
              datetime.now().strftime("%Y%m%d_%H%M%S_%f")).resolve()
    m_values = number_list(args.m_values or ("6" if args.figure == 9 else "4,5,6,7,8,9,10,11,12"), int)
    config = {"outputDir": str(output), "rounds": args.rounds, "warmupRequests": args.warmup_requests,
              "requestsPerRound": args.requests, "mValues": m_values, "pfValues": number_list(args.pf_values),
              "timeoutsSec": number_list(args.timeouts or ("0.08,0.10" if args.figure == 9 else "0.10")),
              "scenarios": ["nonresponding", "malicious"] if args.scenario == "both" else [args.scenario],
              "seed": args.seed, "repositoryFigure": args.figure}
    if args.fixed_faulty_ca_ids is not None:
        config["fixedFaultyCaIds"] = number_list(args.fixed_faulty_ca_ids, int) if args.fixed_faulty_ca_ids.strip() else []
    output.mkdir(parents=True, exist_ok=True)
    config_path = output / "availability_config.json"
    with config_path.open("x", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
    cmd = ["node", str(ROOT / "blockchain/dpki-experiment/run-real-dpki-experiment.js"),
           "--availability-config", str(config_path), "--rpc", args.rpc, "--pow-rpc", args.pow_rpc,
           "--pow-runtime", args.pow_runtime, "--chain-id", args.chain_id, "--pow-warmup-ms", "1000",
           "--lambda-arrival", str(args.lambda_arrival), "--p-manage", str(args.p_manage),
           "--gamma-on-chain", str(args.gamma_on_chain), "--epsilon-points", str(args.epsilon),
           "--service-cas", str(max(m_values)), "--seed", str(args.seed)]
    subprocess.run(cmd, cwd=ROOT, check=True)
    aggregate(output)
    print(f"Raw requests, injection events and independently checked counts: {output}")


if __name__ == "__main__":
    main()
