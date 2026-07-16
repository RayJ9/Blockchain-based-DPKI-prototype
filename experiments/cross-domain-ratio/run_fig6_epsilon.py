from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from figure_dpki_pki_runtime.backend import RunSpec, run_real_experiment  # noqa: E402
from figure_dpki_pki_runtime.epsilon_metrics import (  # noqa: E402
    DEFAULT_EPSILON_POINTS,
    build_points,
    cleanup_legacy_outputs,
    copy_run_logs,
    epsilon_text,
    load_run_spec,
    mirror_final_outputs_to_script_root,
    plot,
    restart_pow,
    run_experiment_from_args,
    stop_pow,
    write_bounds_check,
    write_figure_data,
)


def run_experiment(args: argparse.Namespace) -> Path:
    if args.reuse_run_dir:
        return Path(args.reuse_run_dir).resolve()
    if args.restart_pow:
        restart_pow(args.mean_block_ms)
    return run_experiment_from_args(args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the standalone Fig6 epsilon experiment only.")
    parser.add_argument("--epsilon-points", default=epsilon_text(DEFAULT_EPSILON_POINTS))
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--lambda-arrival", type=float, default=3.0)
    parser.add_argument("--p-manage", type=float, default=0.1)
    parser.add_argument("--gamma-on-chain", type=float, default=0.3)
    parser.add_argument("--q-manage", type=float, default=0.3)
    parser.add_argument("--service-cas", type=int, default=4)
    parser.add_argument("--actual-execution-mode", default="serial", choices=["serial", "parallel"])
    parser.add_argument("--dpki-root-read-mode", default="chain", choices=["chain", "cache", "cached"])
    parser.add_argument("--dpki-proof-read-mode", default="http", choices=["http", "local", "cache", "cached"])
    parser.add_argument("--dpki-proof-base-port", type=int, default=20080)
    parser.add_argument("--fixed-gas-limit", type=int, default=800000)
    parser.add_argument("--fixed-gas-price-wei", default="1")
    parser.add_argument("--raw-tx-submit-timeout-ms", type=int, default=250)
    parser.add_argument("--raw-tx-submit-retries", type=int, default=4)
    parser.add_argument("--raw-tx-receipt-timeout-ms", type=int, default=15000)
    parser.add_argument("--lambda-block", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=61001)
    parser.add_argument("--mean-block-ms", type=int, default=20)
    parser.add_argument("--tag", default="result", help="Compatibility option; default output now uses the fixed result directory.")
    parser.add_argument("--restart-pow", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stop-pow", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--reuse-run-dir", default="")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()
    args.epsilon_values = [float(item.strip()) for item in args.epsilon_points.split(",") if item.strip()]
    if not args.epsilon_values:
        raise SystemExit("--epsilon-points must contain at least one value")
    return args


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else SCRIPT_DIR / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    cleanup_legacy_outputs(output_dir)
    try:
        run_dir = run_experiment(args)
        points, by_kind = build_points(
            run_dir,
            gamma_on_chain_override=args.gamma_on_chain,
            q_manage_override=args.q_manage,
            dpki_q_mode="config",
        )
        by_kind.to_csv(output_dir / "delay_by_request_type.csv", index=False)
        smooth = plot(points, output_dir)
        write_figure_data(points, smooth, output_dir)
        logs_dir = copy_run_logs(run_dir, output_dir)
        write_bounds_check(points, logs_dir)
        run_spec = load_run_spec(run_dir)
        manifest = {
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "runDir": str(run_dir),
            "logsDir": str(logs_dir),
            "requestsPerEpsilon": int(run_spec.get("requests", args.requests)),
            "epsilonPoints": points["epsilon"].astype(float).tolist(),
            "lambdaArrival": float(run_spec.get("lambda_arrival", args.lambda_arrival)),
            "pManage": float(run_spec.get("p_manage", args.p_manage)),
            "gammaOnChain": float(points["gammaOnChainMeasured"].median()),
            "sourceRunGammaOnChain": float(run_spec.get("gamma_on_chain", args.gamma_on_chain)),
            "gammaReplayMode": "reweighted from measured DPKI intra-domain samples",
            "serviceCAs": int(run_spec.get("service_cas", args.service_cas)),
            "fixedGasLimit": int(run_spec.get("fixed_gas_limit", args.fixed_gas_limit)),
            "fixedGasPriceWei": str(run_spec.get("fixed_gas_price_wei", args.fixed_gas_price_wei)),
            "actualExecutionMode": str(run_spec.get("actual_execution_mode", args.actual_execution_mode)),
            "rawTxSubmitTimeoutMs": int(run_spec.get("raw_tx_submit_timeout_ms", args.raw_tx_submit_timeout_ms)),
            "rawTxSubmitRetries": int(run_spec.get("raw_tx_submit_retries", args.raw_tx_submit_retries)),
            "rawTxReceiptTimeoutMs": int(run_spec.get("raw_tx_receipt_timeout_ms", args.raw_tx_receipt_timeout_ms)),
            "dpkiRootReadMode": args.dpki_root_read_mode,
            "dpkiProofReadMode": str(run_spec.get("dpki_proof_read_mode", args.dpki_proof_read_mode)),
            "dpkiProofBasePort": int(run_spec.get("dpki_proof_base_port", args.dpki_proof_base_port)),
            "dpkiAssertionIncluded": True,
            "pkiServiceMetric": "explicit OpenSSL/OCSP/assertion stages; management excludes CA-side OCSP refresh and self OCSP queries",
        }
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
        if output_dir == SCRIPT_DIR / "result":
            mirror_final_outputs_to_script_root(output_dir, SCRIPT_DIR)
            print(f"mirrored final figure files to {SCRIPT_DIR}")
        print(points.to_string(index=False))
        print(f"wrote Fig6 epsilon outputs to {output_dir}")
    finally:
        if args.stop_pow:
            stop_pow()


if __name__ == "__main__":
    main()
