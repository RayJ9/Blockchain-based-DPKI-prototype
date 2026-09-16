"""Audit retained Fig. 9/10 arrays without modifying data or running the prototype.

Requires NumPy. Uses csv.DictReader to preserve Python float parsing rather than
passing source values through the plotting loaders. Formula matches describe
numerical identities, not proof of the historical generating procedure.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def maximum_error(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(np.max(np.abs(actual - expected)))


def survival_factor(pf: np.ndarray, m: np.ndarray, scenario: str) -> np.ndarray:
    if scenario == "responding":
        return 1.0 - pf**m
    result = np.zeros_like(pf)
    for count in np.unique(m):
        mask = m == count
        n = int(count)
        probabilities = pf[mask]
        # Hypothesis checked against the source: fewer than ceil(m / 2) faults.
        result[mask] = sum(
            math.comb(n, k) * probabilities**k * (1 - probabilities)**(n - k)
            for k in range(math.ceil(n / 2))
        )
    return result


def summarize(
    root: Path,
    path: Path,
    scenario: str,
    lower: np.ndarray,
    upper: np.ndarray,
    mean: np.ndarray,
    pf: np.ndarray,
    m: np.ndarray,
    baseline: np.ndarray,
    sample_count: int,
    declared_requests: float | None = None,
) -> dict:
    n = 10000
    half_width = 1.96 * np.sqrt(mean * (1 - mean) / n)
    expected_mean = baseline * survival_factor(pf, m, scenario)
    return {
        "file": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "scenario": scenario,
        "count": int(mean.size),
        "reversed_bounds": int(np.count_nonzero(lower > upper)),
        "outside_bounds": int(np.count_nonzero((mean < lower) | (mean > upper))),
        "max_abs_mean_minus_midpoint": maximum_error(mean, (lower + upper) / 2),
        "wald_formula_hypothesis": {
            "n": n,
            "z": 1.96,
            "lower": "max(0, mean - z * sqrt(mean * (1 - mean) / n))",
            "upper": "min(1, mean + z * sqrt(mean * (1 - mean) / n))",
            "max_abs_lower_error": maximum_error(lower, np.maximum(0, mean - half_width)),
            "max_abs_upper_error": maximum_error(upper, np.minimum(1, mean + half_width)),
        },
        "mean_formula_hypothesis": {
            "baseline": "mean at pf=0, from the same retained data",
            "factor": (
                "1 - pf**m" if scenario == "responding"
                else "sum(comb(m,k)*pf**k*(1-pf)**(m-k), k=0..ceil(m/2)-1)"
            ),
            "max_abs_error": maximum_error(mean, expected_mean),
        },
        "source_summary_dpki_sample_count": sample_count,
        "max_baseline_count_distance_to_integer": maximum_error(
            baseline * sample_count, np.rint(baseline * sample_count)
        ),
        "points_incompatible_with_single_10000_trial_success_fraction": int(
            np.count_nonzero(np.abs(mean * n - np.rint(mean * n)) > 1e-8)
        ),
        "declared_requests_per_grid": declared_requests,
    }


def audit_sources(root: Path) -> list[dict]:
    timeout_dir = root / "experiments/availability-timeout/source_data"
    ca_dir = root / "experiments/availability-service-ca-number/source_data"
    summary = read_csv(timeout_dir / "fig7_service_latency_samples_summary.csv")
    sample_count = int(next(row["count"] for row in summary if row["sample"] == "DPKI intra-off-chain"))
    results = []
    for scenario in ("responding", "malicious"):
        path = timeout_dir / f"surface_data_matrices_{scenario}.npz"
        with np.load(path, allow_pickle=False) as data:
            mean = data["DPKI_MEAN"]
            zero_columns = np.flatnonzero(data["pf_values"] == 0)
            if len(zero_columns) != 1:
                raise ValueError(f"Expected exactly one pf=0 column in {path}")
            baseline = np.broadcast_to(mean[:, zero_columns], mean.shape)
            results.append(summarize(
                root, path, scenario, data["DPKI_LOWER"], data["DPKI_UPPER"], mean,
                data["PF"], np.full(mean.shape, int(data["fixed_m"].item())),
                baseline, sample_count, float(data["requests_per_grid"].item()),
            ))

        path = ca_dir / f"availability_pf_m_slices_{scenario}.csv"
        rows = read_csv(path)
        columns = {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}
        baseline_by_m = {float(row["m"]): float(row["DPKI_Mean"]) for row in rows if float(row["pf"]) == 0}
        baseline = np.array([baseline_by_m[m] for m in columns["m"]])
        results.append(summarize(
            root, path, scenario, columns["DPKI_Lower"], columns["DPKI_Upper"],
            columns["DPKI_Mean"], columns["pf"], columns["m"], baseline, sample_count,
        ))
    return results


def audit_local_probes(root: Path) -> list[dict]:
    """Optional ignored local archives; a fresh public checkout may have none."""
    results = []
    for path in sorted((root / "experiment_artifacts").glob("availability-*/*/results/tail_probe/tail_probe_manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
        session = path.parents[2]
        details = []
        for source in sorted((session / "prototype_run_logs").glob("*/real_simulation_results_by_epsilon_detailed.csv")):
            rows = read_csv(source)
            details.append({
                "file": source.relative_to(root).as_posix(),
                "count": len(rows),
                "model_counts": dict(Counter(row["model"] for row in rows)),
                "columns": list(rows[0]) if rows else [],
            })
        results.append({
            "manifest": path.relative_to(root).as_posix(),
            "sample_count": manifest.get("sampleCount"),
            "scope": manifest.get("scope"),
            "requests": details,
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, help="Optional JSON report; source files are never changed")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    report = {
        "head_commit": commit,
        "scope": "Working-tree source bytes identified by SHA-256; numerical reconstruction, not an injection run or proof of historical provenance",
        "sources": audit_sources(root),
        "local_probes": audit_local_probes(root),
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
