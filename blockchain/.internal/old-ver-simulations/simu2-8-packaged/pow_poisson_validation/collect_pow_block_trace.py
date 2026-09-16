from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any
from urllib import request


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR / "result"


def rpc_call(url: str, method: str, params: list[Any] | None = None, timeout: float = 5.0) -> Any:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    ).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "error" in data and data["error"]:
        raise RuntimeError(f"RPC error from {method}: {data['error']}")
    return data.get("result")


def parse_block_number(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value)
    if text.startswith("0x"):
        return int(text, 16)
    return int(text)


def get_block_number(url: str, timeout: float) -> int:
    return parse_block_number(rpc_call(url, "eth_blockNumber", timeout=timeout))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def collect(args: argparse.Namespace) -> None:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {args.rpc} ...")
    initial_height = get_block_number(args.rpc, args.rpc_timeout_sec)
    print(f"Initial block height: {initial_height}")

    if args.warmup_sec > 0:
        print(f"Warmup for {args.warmup_sec:.1f} s ...")
        time.sleep(args.warmup_sec)

    start_height = get_block_number(args.rpc, args.rpc_timeout_sec)
    start_wall = time.time()
    start_perf = time.perf_counter()
    last_height = start_height
    last_height_elapsed = 0.0

    trace_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    poll_count = 0
    rpc_errors = 0

    print(
        "Collecting for "
        f"{args.duration_sec:.1f} s at poll interval {args.poll_ms:.1f} ms; "
        f"baseline height={start_height}"
    )

    deadline = start_perf + args.duration_sec
    while True:
        loop_start = time.perf_counter()
        if loop_start >= deadline:
            break
        try:
            rpc_start = time.perf_counter()
            height = get_block_number(args.rpc, args.rpc_timeout_sec)
            rpc_end = time.perf_counter()
            poll_count += 1
        except Exception as exc:  # noqa: BLE001
            rpc_errors += 1
            if args.fail_on_rpc_error:
                raise
            print(f"RPC warning: {exc}")
            time.sleep(max(0.001, args.poll_ms / 1000.0))
            continue

        elapsed = rpc_end - start_perf
        poll_latency_ms = (rpc_end - rpc_start) * 1000.0
        if height > last_height:
            delta = height - last_height
            trace_rows.append(
                {
                    "changeIndex": len(trace_rows) + 1,
                    "timestampMs": int((start_wall + elapsed) * 1000),
                    "elapsedSec": f"{elapsed:.9f}",
                    "blockNumber": height,
                    "blockDelta": delta,
                    "pollLatencyMs": f"{poll_latency_ms:.6f}",
                }
            )

            event_rows.append({
                "eventIndex": len(event_rows) + 1,
                "blockNumber": height,
                "timestampMs": int((start_wall + elapsed) * 1000),
                "elapsedSec": f"{elapsed:.9f}",
                "interpolated": "false",
                "sourceDelta": delta,
            })

            last_height = height
            last_height_elapsed = elapsed

        sleep_sec = args.poll_ms / 1000.0 - (time.perf_counter() - loop_start)
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    end_perf = time.perf_counter()
    end_height = get_block_number(args.rpc, args.rpc_timeout_sec)
    duration_sec = end_perf - start_perf
    observed_blocks = max(0, end_height - start_height)
    missing_timestamps = sum(int(row["sourceDelta"]) - 1 for row in event_rows)

    write_csv(
        out_dir / "block_trace.csv",
        trace_rows,
        [
            "changeIndex",
            "timestampMs",
            "elapsedSec",
            "blockNumber",
            "blockDelta",
            "pollLatencyMs",
        ],
    )
    write_csv(
        out_dir / "block_events.csv",
        event_rows,
        [
            "eventIndex",
            "blockNumber",
            "timestampMs",
            "elapsedSec",
            "interpolated",
            "sourceDelta",
        ],
    )

    manifest = {
        "rpc": args.rpc,
        "durationSecRequested": args.duration_sec,
        "durationSecObserved": duration_sec,
        "warmupSec": args.warmup_sec,
        "pollMs": args.poll_ms,
        "rpcTimeoutSec": args.rpc_timeout_sec,
        "initialHeightBeforeWarmup": initial_height,
        "startBlockNumber": start_height,
        "endBlockNumber": end_height,
        "observedBlocksByHeight": observed_blocks,
        "observedEventsRecorded": len(event_rows),
        "heightChangeObservations": len(trace_rows),
        "unobservedBlockTimestamps": missing_timestamps,
        "pollCount": poll_count,
        "rpcErrors": rpc_errors,
        "lambdaByHeightPerSec": observed_blocks / duration_sec if duration_sec > 0 else None,
    }
    (out_dir / "collection_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(
        f"Done. Recorded {len(event_rows)} block events over {duration_sec:.3f} s "
        f"(height delta={observed_blocks}, lambda={manifest['lambdaByHeightPerSec']:.4f}/s)."
    )
    if missing_timestamps:
        print(f"{missing_timestamps} block timestamps were not observed; no timestamps were interpolated.")
    print(f"Output: {out_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect block-height changes from a PoW Chain33/Omnilink RPC endpoint."
    )
    parser.add_argument("--rpc", default="http://127.0.0.1:8545")
    parser.add_argument("--duration-sec", type=float, default=900.0)
    parser.add_argument("--warmup-sec", type=float, default=30.0)
    parser.add_argument("--poll-ms", type=float, default=10.0)
    parser.add_argument("--rpc-timeout-sec", type=float, default=5.0)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--fail-on-rpc-error", action="store_true")
    return parser


def main() -> None:
    collect(build_parser().parse_args())


if __name__ == "__main__":
    main()
