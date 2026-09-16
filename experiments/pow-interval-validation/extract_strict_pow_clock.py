from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
DEFAULT_LOG_DIR = ROOT.parent.parent / "blockchain" / "sidechain-three-chain" / "runtime" / "logs"
DEFAULT_CSV = ROOT / "source_data" / "strict_pow_clock_samples.csv"
DEFAULT_MANIFEST = ROOT / "source_data" / "strict_pow_clock_manifest.json"

DELAY_PATTERN = re.compile(r"poissonDelay=(\S+)")
DURATION_PART = re.compile(r"(\d+(?:\.\d+)?)(ns|us|\u00b5s|\u03bcs|ms|s|m|h)")


def duration_ms(token: str) -> float:
    units = {"ns": 1e-6, "us": 1e-3, "\u00b5s": 1e-3, "\u03bcs": 1e-3,
             "ms": 1.0, "s": 1000.0, "m": 60000.0, "h": 3600000.0}
    value, end = 0.0, 0
    for match in DURATION_PART.finditer(token):
        if match.start() != end:
            raise ValueError(f"Invalid Go duration: {token!r}")
        value += float(match[1]) * units[match[2]]
        end = match.end()
    if not end or end != len(token):
        raise ValueError(f"Invalid Go duration: {token!r}")
    return value


def read_file(path: Path) -> np.ndarray:
    samples: list[float] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if "msg=PowNewBlock" not in line:
                continue
            match = DELAY_PATTERN.search(line)
            if match:
                samples.append(duration_ms(match.group(1)))
    return np.asarray(samples, dtype=float)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract unchanged PowNewBlock.poissonDelay samples from Omnilink logs.")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--sample-count", type=int, default=10_000)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    if args.sample_count < 1:
        parser.error("--sample-count must be positive")
    # Deterministic file order; selection never depends on the sample mean.
    log_files = sorted(args.log_dir.glob("*.log"))
    records = [(path.name, float(value)) for path in log_files for value in read_file(path)]
    if len(records) < args.sample_count:
        raise RuntimeError(f"Only {len(records)} PoW samples found; need {args.sample_count}")
    records = records[:args.sample_count]
    values = np.asarray([value for _, value in records], dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("PoW delays must be finite and positive")
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sampleIndex", "sourceFile", "rawPoissonDelayMs"])
        for index, (source_file, value) in enumerate(records, start=1):
            writer.writerow([index, source_file, value])
    manifest = {
        "source": "Omnilink PowNewBlock.poissonDelay",
        "interpretation": "Logged requested PoW clock delay before block processing; unscaled",
        "logDirectory": str(args.log_dir.resolve()), "sampleCount": len(values),
        "selection": "first N samples in filename/line order; no mean-based filtering",
        "selectedFiles": sorted({name for name, _ in records}),
        "rawMeanMs": float(values.mean()),
        "rawStdMs": float(values.std(ddof=1)) if len(values) > 1 else None,
        "lambdaPerSec": float(1000.0 / values.mean()),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Saved {len(values)} unscaled PoW samples to {args.output_csv}")


if __name__ == "__main__":
    main()
