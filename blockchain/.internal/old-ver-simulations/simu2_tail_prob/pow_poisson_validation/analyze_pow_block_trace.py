from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "result"


def read_events(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    events: list[dict[str, Any]] = []
    for row in rows:
        events.append(
            {
                "blockNumber": int(row["blockNumber"]),
                "elapsedSec": float(row["elapsedSec"]),
                "interpolated": str(row.get("interpolated", "")).lower() == "true",
            }
        )
    events.sort(key=lambda item: (item["blockNumber"], item["elapsedSec"]))
    return events


def ks_distance_exp(samples: np.ndarray, rate: float) -> float:
    x = np.sort(samples)
    n = len(x)
    cdf = 1.0 - np.exp(-rate * x)
    upper = np.arange(1, n + 1) / n
    lower = np.arange(0, n) / n
    return float(np.max(np.maximum(np.abs(upper - cdf), np.abs(cdf - lower))))


def ks_asymptotic_pvalue(d_stat: float, n: int) -> float:
    if n <= 0:
        return math.nan
    x = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d_stat
    total = 0.0
    for j in range(1, 101):
        term = 2.0 * ((-1) ** (j - 1)) * math.exp(-2.0 * j * j * x * x)
        total += term
        if abs(term) < 1e-12:
            break
    return float(max(0.0, min(1.0, total)))


def poisson_pmf_values(mean: float, max_k: int) -> np.ndarray:
    probs = np.zeros(max_k + 1)
    if mean <= 0:
        probs[0] = 1.0
        return probs
    probs[0] = math.exp(-mean)
    for k in range(1, max_k + 1):
        probs[k] = probs[k - 1] * mean / k
    return probs


def lag1_autocorr(values: np.ndarray) -> float:
    if len(values) < 3:
        return math.nan
    x = values[:-1]
    y = values[1:]
    if np.std(x) == 0 or np.std(y) == 0:
        return math.nan
    return float(np.corrcoef(x, y)[0, 1])


def write_dict_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_window_counts(event_times: np.ndarray, duration: float, window_sec: float) -> np.ndarray:
    if duration <= 0 or window_sec <= 0:
        return np.array([], dtype=int)
    full_windows = int(math.floor(duration / window_sec))
    if full_windows <= 0:
        return np.array([], dtype=int)
    counts = np.zeros(full_windows, dtype=int)
    for t in event_times:
        if 0 <= t < full_windows * window_sec:
            idx = int(t // window_sec)
            counts[idx] += 1
    return counts


def analyze(args: argparse.Namespace) -> None:
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    events = read_events(input_dir / "block_events.csv")
    if len(events) < 3:
        raise RuntimeError("Need at least three block events for distribution validation.")

    manifest_path = input_dir / "collection_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    if any(event["interpolated"] for event in events):
        raise ValueError("Interpolated timestamps are not measured block events; collect a new trace")
    interval_rows = []
    intervals = []
    for prev, curr in zip(events[:-1], events[1:]):
        if curr["blockNumber"] != prev["blockNumber"] + 1:
            raise ValueError("Missing block timestamps prevent distribution validation; collect a complete trace")
        delta = curr["elapsedSec"] - prev["elapsedSec"]
        if not math.isfinite(delta) or delta <= 0:
            raise ValueError("Block observations must have finite, strictly increasing timestamps")
        intervals.append(delta)
        interval_rows.append({
            "fromBlock": prev["blockNumber"], "toBlock": curr["blockNumber"],
            "intervalSec": delta,
        })
    selected_intervals = np.asarray(intervals, dtype=float)
    if len(selected_intervals) < 3:
        raise RuntimeError("Need at least three observed block intervals; collect a longer trace")

    mean_interval = float(np.mean(selected_intervals))
    std_interval = float(np.std(selected_intervals, ddof=1))
    cv = std_interval / mean_interval if mean_interval > 0 else math.nan
    lambda_hat = 1.0 / mean_interval if mean_interval > 0 else math.nan
    ks_d = ks_distance_exp(selected_intervals, lambda_hat)
    ks_p = ks_asymptotic_pvalue(ks_d, len(selected_intervals))
    ac1 = lag1_autocorr(selected_intervals)

    event_times = np.asarray([event["elapsedSec"] for event in events], dtype=float)
    duration = float(manifest.get("durationSecObserved") or max(event_times))
    window_sec = args.window_sec if args.window_sec > 0 else max(1.0, 10.0 / lambda_hat)
    counts = make_window_counts(event_times, duration, window_sec)
    window_mean = float(lambda_hat * window_sec)
    max_count = int(max(np.max(counts) if len(counts) else 0, math.ceil(window_mean + 5 * math.sqrt(max(window_mean, 1.0)))))
    pmf = poisson_pmf_values(window_mean, max_count)
    empirical_probs = np.zeros(max_count + 1)
    for k in counts:
        if k <= max_count:
            empirical_probs[k] += 1
    if len(counts):
        empirical_probs /= len(counts)

    write_dict_csv(
        output_dir / "block_intervals.csv",
        interval_rows,
        ["fromBlock", "toBlock", "intervalSec"],
    )

    stat_row = {
        "intervalSource": "observed",
        "intervalCount": len(selected_intervals),
        "meanIntervalSec": mean_interval,
        "stdIntervalSec": std_interval,
        "cv": cv,
        "lambdaHatPerSec": lambda_hat,
        "ksDistanceToFittedExp": ks_d,
        "ksAsymptoticPValueApprox": ks_p,
        "lag1Autocorrelation": ac1,
        "interpolatedBlockFraction": manifest.get("interpolatedBlockFraction", math.nan),
        "windowSec": window_sec,
        "windowCountSamples": len(counts),
        "windowMeanBlocks": window_mean,
    }
    write_dict_csv(
        output_dir / "interarrival_statistics.csv",
        [stat_row],
        list(stat_row.keys()),
    )

    count_rows = [
        {
            "blocksPerWindow": k,
            "empiricalProbability": empirical_probs[k],
            "poissonProbability": pmf[k],
            "windowSec": window_sec,
            "poissonMean": window_mean,
            "windowSamples": len(counts),
        }
        for k in range(max_count + 1)
    ]
    write_dict_csv(
        output_dir / "window_count_distribution.csv",
        count_rows,
        [
            "blocksPerWindow",
            "empiricalProbability",
            "poissonProbability",
            "windowSec",
            "poissonMean",
            "windowSamples",
        ],
    )

    summary = {
        "collectionManifest": manifest,
        "statistics": stat_row,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    plot_figure(output_dir, selected_intervals, lambda_hat, counts, pmf, empirical_probs, window_sec)
    print(
        "PoW validation complete: "
        f"n={len(selected_intervals)}, lambda_hat={lambda_hat:.4f}/s, "
        f"mean={mean_interval:.4f}s, CV={cv:.4f}, KS-distance={ks_d:.4f}, "
        f"lag1={ac1:.4f}"
    )
    print(f"Output: {output_dir}")


def plot_figure(
    output_dir: Path,
    intervals: np.ndarray,
    lambda_hat: float,
    counts: np.ndarray,
    pmf: np.ndarray,
    empirical_probs: np.ndarray,
    window_sec: float,
) -> None:
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 12,
            "legend.fontsize": 9,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "lines.linewidth": 2.0,
            "font.family": "DejaVu Sans",
        }
    )

    sorted_intervals = np.sort(intervals)
    n = len(sorted_intervals)
    ecdf_y = np.arange(1, n + 1) / n
    exp_cdf = 1.0 - np.exp(-lambda_hat * sorted_intervals)

    p = (np.arange(1, n + 1) - 0.5) / n
    theory_q = -np.log(1.0 - p) / lambda_hat
    stride = max(1, n // 1200)

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.7))

    axes[0].step(sorted_intervals, ecdf_y, where="post", color="#1f77b4", label="Measured ECDF")
    axes[0].plot(sorted_intervals, exp_cdf, color="#d62728", linestyle="--", label="Fitted exponential")
    axes[0].set_xlabel("Inter-block interval (s)")
    axes[0].set_ylabel("CDF")
    axes[0].grid(True, linestyle="--", alpha=0.45)
    axes[0].legend(loc="lower right", frameon=True)

    axes[1].scatter(theory_q[::stride], sorted_intervals[::stride], s=12, facecolors="none", edgecolors="#2ca02c")
    lim = max(float(np.max(theory_q)), float(np.max(sorted_intervals)))
    axes[1].plot([0, lim], [0, lim], color="#444444", linestyle="--", label="45-degree line")
    axes[1].set_xlabel("Exponential quantile (s)")
    axes[1].set_ylabel("Measured quantile (s)")
    axes[1].grid(True, linestyle="--", alpha=0.45)
    axes[1].legend(loc="upper left", frameon=True)

    k_values = np.arange(len(pmf))
    width = 0.36
    axes[2].bar(k_values - width / 2, empirical_probs, width=width, color="#4c78a8", alpha=0.75, label="Measured")
    axes[2].bar(k_values + width / 2, pmf, width=width, color="#f58518", alpha=0.75, label="Poisson fit")
    axes[2].set_xlabel(f"Blocks per {window_sec:g}s window")
    axes[2].set_ylabel("Probability")
    axes[2].grid(True, axis="y", linestyle="--", alpha=0.45)
    axes[2].legend(loc="upper right", frameon=True)
    if len(k_values) > 18:
        axes[2].set_xlim(-0.75, min(len(k_values) - 0.25, np.max(counts) + 5 if len(counts) else 18))

    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze PoW block intervals and compare them with fitted exponential/Poisson models."
    )
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--window-sec", type=float, default=0.0, help="Use <=0 for an automatic window with about 10 expected blocks.")
    return parser


def main() -> None:
    analyze(build_parser().parse_args())


if __name__ == "__main__":
    main()
