from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract real latency tail samples from a lightweight availability probe.")
    parser.add_argument("--figure", type=int, choices=[9, 10], required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", default="0.08,0.10,0.12")
    return parser.parse_args()


def load_request_samples(result_dir: Path) -> pd.DataFrame:
    sources_path = result_dir / "logs" / "run_sources.csv"
    if not sources_path.exists():
        raise FileNotFoundError(f"Missing run source index: {sources_path}")
    frames: list[pd.DataFrame] = []
    for source in pd.read_csv(sources_path).get("runDir", pd.Series(dtype=str)).dropna().astype(str).unique():
        run_dir = Path(source)
        detailed = run_dir / "real_simulation_results_by_epsilon_detailed.csv"
        if detailed.exists():
            frame = pd.read_csv(detailed)
            frame["sourceRun"] = str(run_dir)
            frames.append(frame)
    if not frames:
        raise FileNotFoundError("No detailed request samples were found in the indexed experiment runs.")
    return pd.concat(frames, ignore_index=True, sort=False)


def choose_latency_column(frame: pd.DataFrame) -> str:
    for candidate in ("figServiceMs", "serviceMs", "latencyMs", "totalServiceMs", "responseMs"):
        if candidate in frame.columns and pd.to_numeric(frame[candidate], errors="coerce").notna().any():
            return candidate
    raise KeyError("No supported latency column was found in the detailed request samples.")


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = load_request_samples(args.result_dir.resolve())
    latency_col = choose_latency_column(samples)
    samples["tailLatencyMs"] = pd.to_numeric(samples[latency_col], errors="coerce")
    samples = samples[np.isfinite(samples["tailLatencyMs"])].copy()
    if samples.empty:
        raise RuntimeError("The real probe produced no finite latency samples.")

    group_columns = [column for column in ("model", "kind", "requestType") if column in samples.columns]
    if not group_columns:
        samples["model"] = "all"
        group_columns = ["model"]

    rows: list[dict[str, object]] = []
    timeout_values = [float(item) for item in args.timeout_seconds.split(",") if item.strip()]
    for keys, group in samples.groupby(group_columns, dropna=False):
        key_values = keys if isinstance(keys, tuple) else (keys,)
        base = dict(zip(group_columns, key_values))
        values = group["tailLatencyMs"].to_numpy(dtype=float)
        summary = {
            **base,
            "count": int(values.size),
            "meanMs": float(np.mean(values)),
            "stdMs": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
            "p90Ms": float(np.quantile(values, 0.90)),
            "p95Ms": float(np.quantile(values, 0.95)),
            "p99Ms": float(np.quantile(values, 0.99)),
            "maxMs": float(np.max(values)),
        }
        for timeout in timeout_values:
            summary[f"availabilityAt{timeout:.3f}s"] = float(np.mean(values <= timeout * 1000.0))
        rows.append(summary)

    pd.DataFrame(rows).to_csv(output_dir / "tail_summary.csv", index=False)
    samples.sort_values("tailLatencyMs", ascending=False).head(200).to_csv(output_dir / "tail_samples.csv", index=False)
    manifest = {
        "figure": args.figure,
        "sourceResultDir": str(args.result_dir.resolve()),
        "latencyColumn": latency_col,
        "sampleCount": int(len(samples)),
        "timeoutSeconds": timeout_values,
        "scope": "lightweight real-chain tail probe; retained availability surfaces are not overwritten",
    }
    (output_dir / "tail_probe_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"Saved tail probe to {output_dir}")


if __name__ == "__main__":
    main()
