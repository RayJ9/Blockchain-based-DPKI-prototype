from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_LOG_DIR = ROOT.parent.parent / "pow-4nodes-runtime" / "runtime" / "node0" / "logs"
DEFAULT_CSV = ROOT / "source_data" / "strict_pow_clock_samples.csv"
DEFAULT_MANIFEST = ROOT / "source_data" / "strict_pow_clock_manifest.json"

DELAY_PATTERN = re.compile(r"poissonDelay=([^ ]+)")
NUMBER_PATTERN = re.compile(r"^[0-9.]+")


def duration_ms(token: str) -> float:
    match = NUMBER_PATTERN.match(token)
    if not match:
        raise ValueError(f"Invalid Go duration: {token!r}")
    value = float(match.group(0))
    if token.endswith("ms"):
        return value
    if chr(181) in token or token.endswith("us"):
        return value * 1e-3
    if token.endswith("ns"):
        return value * 1e-6
    if token.endswith("s"):
        return value * 1000.0
    raise ValueError(f"Unsupported Go duration: {token!r}")


def read_file(path: Path) -> np.ndarray:
    samples: list[float] = []
    with path.open("r", encoding="latin1") as handle:
        for line in handle:
            if "msg=PowNewBlock" not in line:
                continue
            match = DELAY_PATTERN.search(line)
            if match:
                samples.append(duration_ms(match.group(1)))
    return np.asarray(samples, dtype=float)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract the strict exponential PoW clock from Omnilink logs."
    )
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--sample-count", type=int, default=10_000)
    parser.add_argument("--target-mean-ms", type=float, default=101.7)
    parser.add_argument("--stable-rate-tolerance", type=float, default=0.15)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    log_files = sorted(args.log_dir.glob("*.log"), key=lambda path: path.stat().st_mtime)
    file_samples = [(path, read_file(path)) for path in log_files]
    file_samples = [(path, values) for path, values in file_samples if len(values) >= 100]
    if not file_samples:
        raise RuntimeError(f"No PowNewBlock poissonDelay samples found in {args.log_dir}")

    file_means = np.asarray([values.mean() for _, values in file_samples], dtype=float)
    median_file_mean = float(np.median(file_means))
    selected = [
        (path, values)
        for path, values in file_samples
        if abs(float(values.mean()) - median_file_mean) / median_file_mean
        <= args.stable_rate_tolerance
    ]

    records: list[tuple[str, float]] = []
    for path, values in selected:
        records.extend((path.name, float(value)) for value in values)
    if len(records) < args.sample_count:
        raise RuntimeError(
            f"Only {len(records)} stable-rate samples found; need {args.sample_count}."
        )

    records = records[: args.sample_count]
    raw_values = np.asarray([value for _, value in records], dtype=float)
    scale_factor = args.target_mean_ms / float(raw_values.mean())
    calibrated_values = raw_values * scale_factor

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "sampleIndex",
                "sourceFile",
                "rawPoissonDelayMs",
                "calibratedPoissonDelayMs",
            ]
        )
        for index, ((source_file, raw_value), calibrated_value) in enumerate(
            zip(records, calibrated_values), start=1
        ):
            writer.writerow([index, source_file, f"{raw_value:.9f}", f"{calibrated_value:.9f}"])

    manifest = {
        "source": "Omnilink PowNewBlock.poissonDelay",
        "interpretation": "Strict PoW exponential clock before block processing",
        "logDirectory": str(args.log_dir.resolve()),
        "sampleCount": int(len(calibrated_values)),
        "stableRateMedianFileMeanMs": median_file_mean,
        "stableRateTolerance": args.stable_rate_tolerance,
        "selectedFiles": [path.name for path, _ in selected],
        "rawMeanMs": float(raw_values.mean()),
        "targetMeanMs": args.target_mean_ms,
        "scaleFactor": scale_factor,
        "calibratedMeanMs": float(calibrated_values.mean()),
        "calibratedStdMs": float(calibrated_values.std(ddof=1)),
        "calibratedCv": float(calibrated_values.std(ddof=1) / calibrated_values.mean()),
        "lambdaPerSec": float(1000.0 / calibrated_values.mean()),
    }
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Saved {args.output_csv}")
    print(f"Saved {args.manifest}")
    print(
        "Strict PoW clock: "
        f"N={len(calibrated_values)}, mean={calibrated_values.mean():.3f} ms, "
        f"CV={manifest['calibratedCv']:.4f}, lambda={manifest['lambdaPerSec']:.4f}/s"
    )


if __name__ == "__main__":
    main()
