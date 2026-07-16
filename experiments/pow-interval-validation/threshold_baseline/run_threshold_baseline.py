from __future__ import annotations

import argparse
import base64
import contextlib
import json
import math
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pandas as pd
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent
ANCHOR_CSV = ROOT / "source_data" / "summary_by_request_class_fig7_aligned.csv"
if not ANCHOR_CSV.exists():
    ANCHOR_CSV = ROOT / "source_data" / "summary_by_request_class_no_authsig.csv"
SERVICE_PROBE_ROOT = ROOT.parent.parent / "simu2-8-packaged" / "service_probe"

SUMMARY_COLUMNS = [
    "mechanism",
    "requestClass",
    "rounds",
    "meanRawLatencyMs",
    "medianRawLatencyMs",
    "p95RawLatencyMs",
    "meanNormalizedLatencyMs",
    "medianNormalizedLatencyMs",
    "p95NormalizedLatencyMs",
    "meanGasUsed",
    "meanTxInputBytes",
    "meanRawTxBytes",
    "meanReceiptLogBytes",
    "meanStateWriteBytesEstimated",
    "meanChainReads",
    "meanProofNodes",
    "meanVerifiedCertificateSteps",
    "meanIssueUpdateMs",
    "meanStatusValidationMs",
    "meanCertVerificationMs",
    "meanSignatureMs",
    "meanContractExecutionMs",
]


@dataclass(frozen=True)
class Anchor:
    issue_update_ms: float
    cert_management_ms: float
    cert_intra_ms: float
    cert_intra_onchain_ms: float
    cert_cross_ms: float
    contract_management_ms: float
    contract_intra_ms: float
    contract_cross_ms: float
    gas_management: float
    gas_intra: float
    gas_cross: float


@dataclass(frozen=True)
class ValidatorEndpoint:
    validator_id: int
    url: str
    public_key: object


class ValidatorHttpServer(ThreadingHTTPServer):
    allow_reuse_address = True


class ValidatorHandler(BaseHTTPRequestHandler):
    server: ValidatorHttpServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        if self.path != "/validate":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            request = json.loads(body.decode("utf-8"))
            request_class = str(request["requestClass"])
            payload = base64.b64decode(str(request["payloadB64"]).encode("ascii"))
            delay_ms = self.server.next_delay_ms(request_class)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            signature = self.server.validator_key.sign(payload)
            response = {
                "validatorId": self.server.validator_id,
                "delayMs": delay_ms,
                "signatureB64": base64.b64encode(signature).decode("ascii"),
            }
            data = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            data = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)


def request_multiplier(request_class: str) -> float:
    if request_class == "management":
        return 1.15
    if request_class == "cross-on-chain":
        return 1.30
    if request_class == "intra-on-chain":
        return 1.05
    return 1.00


def positive_lognormal(rng: np.random.Generator, mean_ms: float, cv: float) -> float:
    if mean_ms <= 0:
        return 0.0
    if cv <= 0:
        return mean_ms
    sigma = math.sqrt(math.log(1.0 + cv * cv))
    mu = math.log(mean_ms) - 0.5 * sigma * sigma
    return float(rng.lognormal(mu, sigma))


def attach_validator_runtime(
    server: ValidatorHttpServer,
    validator_id: int,
    key: Ed25519PrivateKey,
    rtt_mean_ms: float,
    rtt_cv: float,
    seed: int,
) -> None:
    server.validator_id = validator_id
    server.validator_key = key
    server.rtt_mean_ms = rtt_mean_ms
    server.rtt_cv = rtt_cv
    server.rng = np.random.default_rng(seed)
    server.rng_lock = threading.Lock()

    def next_delay_ms(request_class: str) -> float:
        with server.rng_lock:
            return positive_lognormal(
                server.rng,
                server.rtt_mean_ms * request_multiplier(request_class),
                server.rtt_cv,
            )

    server.next_delay_ms = next_delay_ms


@contextlib.contextmanager
def validator_http_cluster(
    keys: list[Ed25519PrivateKey],
    base_port: int,
    rtt_mean_ms: float,
    rtt_cv: float,
    seed: int,
):
    servers: list[ValidatorHttpServer] = []
    threads: list[threading.Thread] = []
    endpoints: list[ValidatorEndpoint] = []
    try:
        for index, key in enumerate(keys):
            port = base_port + index
            server = ValidatorHttpServer(("127.0.0.1", port), ValidatorHandler)
            attach_validator_runtime(
                server,
                validator_id=index,
                key=key,
                rtt_mean_ms=rtt_mean_ms,
                rtt_cv=rtt_cv,
                seed=seed + index * 1009,
            )
            thread = threading.Thread(target=server.serve_forever, name=f"threshold-validator-{index}", daemon=True)
            thread.start()
            servers.append(server)
            threads.append(thread)
            endpoints.append(
                ValidatorEndpoint(
                    validator_id=index,
                    url=f"http://127.0.0.1:{port}/validate",
                    public_key=key.public_key(),
                )
            )
        yield endpoints
    finally:
        for server in servers:
            server.shutdown()
        for server in servers:
            server.server_close()
        for thread in threads:
            thread.join(timeout=2.0)


def real_management_issue_ms(service_probe_root: Path) -> float | None:
    path = service_probe_root / "management" / "stage_statistics.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    rows = df[
        (df["model"] == "DPKI")
        & (df["kind"] == "management")
        & (df["stage"] == "dpkiManagementIssueCertificate")
    ]
    if len(rows) != 1:
        return None
    return float(rows.iloc[0]["meanMs"])


def load_anchor(path: Path, service_probe_root: Path = SERVICE_PROBE_ROOT) -> Anchor:
    df = pd.read_csv(path)

    def row(mechanism: str, request_class: str) -> pd.Series:
        rows = df[(df["mechanism"] == mechanism) & (df["requestClass"] == request_class)]
        if len(rows) != 1:
            raise ValueError(f"Expected one anchor row for {mechanism}/{request_class}, got {len(rows)}")
        return rows.iloc[0]

    dpki_mgmt = row("proposed-dpki", "management")
    dpki_intra = row("proposed-dpki", "intra-on-chain")
    dpki_cross = row("proposed-dpki", "cross-on-chain")
    dpki_off = row("proposed-dpki", "intra-off-chain")

    issue_update_ms = real_management_issue_ms(service_probe_root)
    if issue_update_ms is None:
        issue_update_ms = float(dpki_mgmt["meanIssueUpdateMs"])

    return Anchor(
        issue_update_ms=issue_update_ms,
        cert_management_ms=float(dpki_mgmt["meanCertVerificationMs"]),
        cert_intra_ms=float(dpki_off["meanCertVerificationMs"]),
        cert_intra_onchain_ms=float(dpki_intra["meanCertVerificationMs"]),
        cert_cross_ms=float(dpki_cross["meanCertVerificationMs"]),
        contract_management_ms=float(dpki_mgmt["meanContractExecutionMs"]),
        contract_intra_ms=float(dpki_intra["meanContractExecutionMs"]),
        contract_cross_ms=float(dpki_cross["meanContractExecutionMs"]),
        gas_management=float(dpki_mgmt["meanGasUsed"]),
        gas_intra=float(dpki_intra["meanGasUsed"]),
        gas_cross=float(dpki_cross["meanGasUsed"]),
    )


def make_validator_keys(n: int) -> list[Ed25519PrivateKey]:
    return [Ed25519PrivateKey.generate() for _ in range(n)]


def measure_threshold_crypto_ms(
    validators: list[Ed25519PrivateKey],
    k: int,
    payload: bytes,
) -> tuple[float, int]:
    selected = validators[:k]
    start = time.perf_counter()
    signatures = [key.sign(payload) for key in selected]
    for key, sig in zip(selected, signatures):
        key.public_key().verify(sig, payload)
    return (time.perf_counter() - start) * 1000.0, len(signatures)


def kth_validator_window_ms(
    rng: np.random.Generator,
    n: int,
    k: int,
    rtt_mean_ms: float,
    cv: float,
    multiplier: float = 1.0,
) -> float:
    samples = [positive_lognormal(rng, rtt_mean_ms * multiplier, cv) for _ in range(n)]
    samples.sort()
    return float(samples[k - 1])


def request_validator(endpoint: ValidatorEndpoint, request_class: str, payload: bytes, timeout_ms: float) -> dict[str, object]:
    request_body = json.dumps(
        {
            "requestClass": request_class,
            "payloadB64": base64.b64encode(payload).decode("ascii"),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint.url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=max(timeout_ms / 1000.0, 0.1)) as response:
        if response.status != 200:
            raise RuntimeError(f"validator {endpoint.validator_id} returned HTTP {response.status}")
        data = json.loads(response.read().decode("utf-8"))
    signature = base64.b64decode(str(data["signatureB64"]).encode("ascii"))
    endpoint.public_key.verify(signature, payload)
    return {
        "validatorId": int(data["validatorId"]),
        "delayMs": float(data.get("delayMs", 0.0)),
        "signature": signature,
    }


def threshold_http_validation_ms(
    endpoints: list[ValidatorEndpoint],
    executor: ThreadPoolExecutor,
    k: int,
    request_class: str,
    payload: bytes,
    timeout_ms: float,
) -> tuple[float, int]:
    start = time.perf_counter()
    valid = 0
    futures = [executor.submit(request_validator, endpoint, request_class, payload, timeout_ms) for endpoint in endpoints]
    measured_ms = None
    errors: list[str] = []
    try:
        for future in as_completed(futures, timeout=max(timeout_ms / 1000.0, 0.1)):
            try:
                future.result()
                valid += 1
                if valid >= k:
                    measured_ms = (time.perf_counter() - start) * 1000.0
                    break
            except Exception as exc:
                errors.append(str(exc))
        if measured_ms is None:
            raise RuntimeError(f"threshold validation collected {valid}/{k} valid endorsements; errors={errors[:3]}")
        return measured_ms, valid
    finally:
        for future in futures:
            future.cancel()


def onchain_costs(request_class: str, anchor: Anchor) -> tuple[float, float, float, float, float]:
    if request_class == "management":
        return (
            anchor.gas_management * 1.08,
            320.0,
            420.0,
            288.0,
            320.0,
        )
    if request_class == "intra-on-chain":
        return (
            anchor.gas_intra * 1.07,
            560.0,
            660.0,
            192.0,
            352.0,
        )
    if request_class == "cross-on-chain":
        return (
            anchor.gas_cross * 1.08,
            640.0,
            740.0,
            192.0,
            384.0,
        )
    return (0.0, 0.0, 0.0, 0.0, 0.0)


def contract_stage_ms(
    rng: np.random.Generator,
    request_class: str,
    anchor: Anchor,
    cv: float,
) -> float:
    if request_class == "management":
        return positive_lognormal(rng, anchor.contract_management_ms * 1.03, cv)
    if request_class == "intra-on-chain":
        return positive_lognormal(rng, anchor.contract_intra_ms * 1.03, cv)
    if request_class == "cross-on-chain":
        return positive_lognormal(rng, anchor.contract_cross_ms * 1.03, cv)
    return 0.0


def cert_stage_ms(
    rng: np.random.Generator,
    request_class: str,
    anchor: Anchor,
    cv: float,
) -> tuple[float, int]:
    if request_class == "cross-on-chain":
        base = anchor.cert_cross_ms
        steps = 2
    elif request_class == "management":
        base = anchor.cert_management_ms
        steps = 2
    elif request_class == "intra-on-chain":
        base = anchor.cert_intra_onchain_ms
        steps = 1
    else:
        base = anchor.cert_intra_ms
        steps = 1
    return positive_lognormal(rng, base, cv), steps


def issue_stage_ms(rng: np.random.Generator, request_class: str, anchor: Anchor, cv: float) -> float:
    if request_class != "management":
        return 0.0
    return positive_lognormal(rng, anchor.issue_update_ms, cv)


def status_stage_ms(
    rng: np.random.Generator,
    request_class: str,
    validators: list[Ed25519PrivateKey],
    k: int,
    payload: bytes,
    rtt_mean_ms: float,
    rtt_cv: float,
    endpoints: list[ValidatorEndpoint] | None = None,
    executor: ThreadPoolExecutor | None = None,
    timeout_ms: float = 2000.0,
) -> tuple[float, int]:
    if endpoints is not None and executor is not None:
        return threshold_http_validation_ms(endpoints, executor, k, request_class, payload, timeout_ms)
    multiplier = request_multiplier(request_class)
    network_window = kth_validator_window_ms(rng, len(validators), k, rtt_mean_ms, rtt_cv, multiplier)
    crypto_ms, sigs = measure_threshold_crypto_ms(validators, k, payload)
    return network_window + crypto_ms, sigs


def simulate(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame]:
    if args.threshold > args.validators:
        raise ValueError("--threshold must be <= --validators")
    rng = np.random.default_rng(args.seed)
    anchor = load_anchor(Path(args.anchor_csv), Path(args.service_probe_root))
    validators = make_validator_keys(args.validators)

    request_classes = [
        "management",
        "intra-off-chain",
        "intra-on-chain",
        "cross-on-chain",
    ]
    rows = []
    if args.http_validators:
        context = validator_http_cluster(
            validators,
            args.validator_base_port,
            args.validator_rtt_mean_ms,
            args.validator_rtt_cv,
            args.seed + 50000,
        )
    else:
        context = contextlib.nullcontext(None)

    with context as endpoints:
        client_workers = args.client_workers if args.client_workers > 0 else max(args.validators * 4, args.validators)
        with ThreadPoolExecutor(max_workers=client_workers) as executor:
            for request_class in request_classes:
                for i in range(args.rounds):
                    payload = (
                        f"threshold-validation-dpki|{request_class}|{i}|{args.seed}".encode("utf-8")
                        + os.urandom(32)
                    )
                    issue_ms = issue_stage_ms(rng, request_class, anchor, args.anchor_cv)
                    cert_ms, cert_steps = cert_stage_ms(rng, request_class, anchor, args.anchor_cv)
                    status_ms, signature_count = status_stage_ms(
                        rng,
                        request_class,
                        validators,
                        args.threshold,
                        payload,
                        args.validator_rtt_mean_ms,
                        args.validator_rtt_cv,
                        endpoints=endpoints,
                        executor=executor if endpoints is not None else None,
                        timeout_ms=args.validator_timeout_ms,
                    )
                    contract_ms = contract_stage_ms(rng, request_class, anchor, args.contract_cv)
                    gas, tx_input, raw_tx, receipt_log, state_bytes = onchain_costs(request_class, anchor)
                    normalized_ms = issue_ms + cert_ms + status_ms + contract_ms
                    rows.append(
                        {
                            "mechanism": "threshold-validation-dpki",
                            "requestClass": request_class,
                            "requestIndex": i,
                            "validators": args.validators,
                            "threshold": args.threshold,
                            "signatureCount": signature_count,
                            "rawLatencyMs": normalized_ms,
                            "normalizedLatencyMs": normalized_ms,
                            "issueUpdateMs": issue_ms,
                            "statusValidationMs": status_ms,
                            "certVerificationMs": cert_ms,
                            "signatureMs": 0.0,
                            "contractExecutionMs": contract_ms,
                            "gasUsed": gas,
                            "txInputBytes": tx_input,
                            "rawTxBytes": raw_tx,
                            "receiptLogBytes": receipt_log,
                            "stateWriteBytesEstimated": state_bytes,
                            "chainReads": 0.0,
                            "proofNodes": 0.0,
                            "verifiedCertificateSteps": float(cert_steps),
                        }
                    )
    metrics = pd.DataFrame(rows)
    summary = summarize(metrics)
    return metrics, summary


def percentile95(values: pd.Series) -> float:
    return float(np.percentile(values.to_numpy(dtype=float), 95))


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    summary_rows = []
    for (mechanism, request_class), group in metrics.groupby(["mechanism", "requestClass"], sort=True):
        summary_rows.append(
            {
                "mechanism": mechanism,
                "requestClass": request_class,
                "rounds": int(len(group)),
                "meanRawLatencyMs": float(group["rawLatencyMs"].mean()),
                "medianRawLatencyMs": float(group["rawLatencyMs"].median()),
                "p95RawLatencyMs": percentile95(group["rawLatencyMs"]),
                "meanNormalizedLatencyMs": float(group["normalizedLatencyMs"].mean()),
                "medianNormalizedLatencyMs": float(group["normalizedLatencyMs"].median()),
                "p95NormalizedLatencyMs": percentile95(group["normalizedLatencyMs"]),
                "meanGasUsed": float(group["gasUsed"].mean()),
                "meanTxInputBytes": float(group["txInputBytes"].mean()),
                "meanRawTxBytes": float(group["rawTxBytes"].mean()),
                "meanReceiptLogBytes": float(group["receiptLogBytes"].mean()),
                "meanStateWriteBytesEstimated": float(group["stateWriteBytesEstimated"].mean()),
                "meanChainReads": float(group["chainReads"].mean()),
                "meanProofNodes": float(group["proofNodes"].mean()),
                "meanVerifiedCertificateSteps": float(group["verifiedCertificateSteps"].mean()),
                "meanIssueUpdateMs": float(group["issueUpdateMs"].mean()),
                "meanStatusValidationMs": float(group["statusValidationMs"].mean()),
                "meanCertVerificationMs": float(group["certVerificationMs"].mean()),
                "meanSignatureMs": float(group["signatureMs"].mean()),
                "meanContractExecutionMs": float(group["contractExecutionMs"].mean()),
            }
        )
    return pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)


def write_outputs(metrics: pd.DataFrame, summary: pd.DataFrame, args: argparse.Namespace) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = OUT_DIR / "threshold_request_metrics.csv"
    summary_path = OUT_DIR / "threshold_summary_by_request_class.csv"
    combined_path = OUT_DIR / "summary_with_threshold_baseline.csv"
    config_path = OUT_DIR / "threshold_config.json"

    metrics.to_csv(metrics_path, index=False)
    summary.to_csv(summary_path, index=False)

    existing = pd.read_csv(args.anchor_csv)
    combined = pd.concat([existing, summary], ignore_index=True)
    combined.to_csv(combined_path, index=False)

    config = {
        "mechanism": "threshold-validation-dpki",
        "description": "k-of-n validator endorsement baseline; assertion is included in certificate verification stage.",
        "anchorCsv": str(Path(args.anchor_csv).resolve()),
        "serviceProbeRoot": str(Path(args.service_probe_root).resolve()),
        "roundsPerRequestClass": args.rounds,
        "validators": args.validators,
        "threshold": args.threshold,
        "httpValidators": args.http_validators,
        "validatorBasePort": args.validator_base_port,
        "validatorPorts": [args.validator_base_port + i for i in range(args.validators)] if args.http_validators else [],
        "validatorTimeoutMs": args.validator_timeout_ms,
        "clientWorkers": args.client_workers if args.client_workers > 0 else max(args.validators * 4, args.validators),
        "validatorRttMeanMs": args.validator_rtt_mean_ms,
        "validatorRttCv": args.validator_rtt_cv,
        "anchorCv": args.anchor_cv,
        "contractCv": args.contract_cv,
        "seed": args.seed,
        "outputs": {
            "requestMetrics": str(metrics_path.name),
            "summary": str(summary_path.name),
            "combinedSummary": str(combined_path.name),
        },
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    print(f"Wrote {metrics_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {combined_path}")
    print(f"Wrote {config_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the threshold-validation DPKI baseline without modifying existing figures."
    )
    parser.add_argument("--rounds", type=int, default=2000, help="Requests per request class.")
    parser.add_argument("--validators", type=int, default=8, help="Number of validators n.")
    parser.add_argument("--threshold", type=int, default=4, help="Threshold k.")
    parser.add_argument("--http-validators", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--validator-base-port", type=int, default=23080)
    parser.add_argument("--validator-timeout-ms", type=float, default=5000.0)
    parser.add_argument("--client-workers", type=int, default=0, help="HTTP client worker pool size; 0 uses 4*n.")
    parser.add_argument("--validator-rtt-mean-ms", type=float, default=28.0)
    parser.add_argument("--validator-rtt-cv", type=float, default=0.35)
    parser.add_argument("--anchor-cv", type=float, default=0.18)
    parser.add_argument("--contract-cv", type=float, default=0.28)
    parser.add_argument("--seed", type=int, default=73001)
    parser.add_argument("--anchor-csv", default=str(ANCHOR_CSV))
    parser.add_argument("--service-probe-root", default=str(SERVICE_PROBE_ROOT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics, summary = simulate(args)
    write_outputs(metrics, summary, args)
    print(summary[["mechanism", "requestClass", "meanNormalizedLatencyMs", "meanStatusValidationMs", "meanCertVerificationMs", "meanContractExecutionMs"]].to_string(index=False))


if __name__ == "__main__":
    main()
