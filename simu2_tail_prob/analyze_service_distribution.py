from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def ks_against_exponential(samples_ms: np.ndarray) -> float:
    if samples_ms.size == 0:
        return float("nan")
    mean_ms = float(samples_ms.mean())
    if mean_ms <= 0:
        return float("nan")
    normalized = np.sort(samples_ms / mean_ms)
    n = normalized.size
    empirical_right = np.arange(1, n + 1, dtype=float) / n
    empirical_left = np.arange(0, n, dtype=float) / n
    theoretical = 1.0 - np.exp(-normalized)
    return float(
        max(
            np.max(np.abs(empirical_right - theoretical)),
            np.max(np.abs(theoretical - empirical_left)),
        )
    )


def quantile_error_row(samples_ms: np.ndarray, probability: float) -> tuple[float, float]:
    mean_ms = float(samples_ms.mean())
    empirical = float(np.quantile(samples_ms, probability))
    theoretical = float(-mean_ms * np.log(max(1e-12, 1.0 - probability)))
    return empirical, theoretical


def summarize_group(group: pd.DataFrame) -> dict[str, float | str | int]:
    samples_ms = pd.to_numeric(group["serviceMs"], errors="coerce").dropna().to_numpy(dtype=float)
    samples_ms = samples_ms[samples_ms > 0]
    count = int(samples_ms.size)
    mean_ms = float(samples_ms.mean()) if count else float("nan")
    std_ms = float(samples_ms.std(ddof=0)) if count else float("nan")
    cv = std_ms / mean_ms if mean_ms > 0 else float("nan")
    ks = ks_against_exponential(samples_ms)
    p50_emp, p50_theory = quantile_error_row(samples_ms, 0.50) if count else (float("nan"), float("nan"))
    p90_emp, p90_theory = quantile_error_row(samples_ms, 0.90) if count else (float("nan"), float("nan"))
    p95_emp, p95_theory = quantile_error_row(samples_ms, 0.95) if count else (float("nan"), float("nan"))
    return {
        "model": str(group["model"].iloc[0]),
        "kind": str(group["kind"].iloc[0]),
        "count": count,
        "meanMs": mean_ms,
        "stdMs": std_ms,
        "cv": cv,
        "cvGapToExp": abs(cv - 1.0) if np.isfinite(cv) else float("nan"),
        "expKs": ks,
        "p50EmpMs": p50_emp,
        "p50ExpMs": p50_theory,
        "p50AbsErrMs": abs(p50_emp - p50_theory) if np.isfinite(p50_emp) and np.isfinite(p50_theory) else float("nan"),
        "p90EmpMs": p90_emp,
        "p90ExpMs": p90_theory,
        "p90AbsErrMs": abs(p90_emp - p90_theory) if np.isfinite(p90_emp) and np.isfinite(p90_theory) else float("nan"),
        "p95EmpMs": p95_emp,
        "p95ExpMs": p95_theory,
        "p95AbsErrMs": abs(p95_emp - p95_theory) if np.isfinite(p95_emp) and np.isfinite(p95_theory) else float("nan"),
        "maxMs": float(samples_ms.max()) if count else float("nan"),
        "p99Ms": float(np.quantile(samples_ms, 0.99)) if count else float("nan"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check how close service times are to an exponential distribution.")
    parser.add_argument("detailed_csv", type=Path, help="Path to real_simulation_results_by_epsilon_detailed.csv")
    parser.add_argument("--output", type=Path, required=True, help="Output CSV path")
    args = parser.parse_args()

    frame = pd.read_csv(args.detailed_csv)
    if "model" not in frame.columns or "kind" not in frame.columns or "serviceMs" not in frame.columns:
      raise SystemExit("Input CSV must contain model, kind, and serviceMs columns")

    rows = [summarize_group(group) for _, group in frame.groupby(["model", "kind"], sort=True)]
    out = pd.DataFrame(rows).sort_values(["model", "kind"]).reset_index(drop=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
