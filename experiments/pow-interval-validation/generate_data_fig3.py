from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


FIG_NAME = "fig3"
ROOT = Path(__file__).resolve().parent
POW_CSV = ROOT / "source_data" / "strict_pow_clock_samples.csv"
DATA_FILE = ROOT / f"data_{FIG_NAME}.mat"


def fmt_ms_rate(ms: float) -> str:
    return f"{1000.0 / ms:.1f} 1/s ({ms:.1f} ms)"


def fmt_ms_rate_range(values_ms: list[float]) -> str:
    rates = [1000.0 / v for v in values_ms]
    return f"{min(rates):.1f}-{max(rates):.1f} 1/s ({min(values_ms):.1f}-{max(values_ms):.1f} ms)"


def main() -> None:
    if not POW_CSV.exists():
        raise FileNotFoundError(
            f"Missing strict PoW samples: {POW_CSV}. Run extract_strict_pow_clock.py first."
        )

    df = pd.read_csv(POW_CSV)
    intervals_ms = df["rawPoissonDelayMs"].to_numpy(dtype=float)
    sample_count = len(intervals_ms)
    mean_ms = float(np.mean(intervals_ms))
    std_ms = float(np.std(intervals_ms, ddof=1))
    cv = std_ms / mean_ms
    lambda_per_sec = 1000.0 / mean_ms
    x_grid_ms = np.linspace(0.0, 5.0 * mean_ms, 600)
    lambda_per_ms = 1.0 / mean_ms
    exp_pdf = lambda_per_ms * np.exp(-lambda_per_ms * x_grid_ms)

    savemat(
        DATA_FILE,
        {
            "intervalsMs": intervals_ms.reshape(-1, 1),
            "xGridMs": x_grid_ms.reshape(-1, 1),
            "expPdf": exp_pdf.reshape(-1, 1),
            "sampleCount": np.array([[sample_count]], dtype=float),
            "meanMs": np.array([[mean_ms]], dtype=float),
            "stdMs": np.array([[std_ms]], dtype=float),
            "cv": np.array([[cv]], dtype=float),
            "lambdaPerSec": np.array([[lambda_per_sec]], dtype=float),
        },
    )
    print(f"Saved {DATA_FILE}")


if __name__ == "__main__":
    main()
