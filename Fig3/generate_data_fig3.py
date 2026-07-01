from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat, savemat


FIG_NAME = "fig3"
ROOT = Path(__file__).resolve().parent
SUMMARY_CSV = ROOT / "source_data" / "summary_by_request_class_fig7_aligned.csv"
if not SUMMARY_CSV.exists():
    SUMMARY_CSV = ROOT / "source_data" / "summary_by_request_class_no_authsig.csv"
POW_MAT = ROOT / "source_data" / "data_pow_exponential.mat"
DATA_FILE = ROOT / f"data_{FIG_NAME}.mat"


def fmt_ms_rate(ms: float) -> str:
    return f"{1000.0 / ms:.1f} 1/s ({ms:.1f} ms)"


def fmt_ms_rate_range(values_ms: list[float]) -> str:
    rates = [1000.0 / v for v in values_ms]
    return f"{min(rates):.1f}-{max(rates):.1f} 1/s ({min(values_ms):.1f}-{max(values_ms):.1f} ms)"


def main() -> None:
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Missing source CSV: {SUMMARY_CSV}")
    if not POW_MAT.exists():
        raise FileNotFoundError(f"Missing PoW data: {POW_MAT}")

    df = pd.read_csv(SUMMARY_CSV)
    pow_data = loadmat(POW_MAT)

    def latency(mechanism: str, request_class: str) -> float:
        row = df[(df.mechanism == mechanism) & (df.requestClass == request_class)].iloc[0]
        return float(row["meanNormalizedLatencyMs"])

    dpki_mgmt_ms = latency("proposed-dpki", "management")
    dpki_auth_ms = [
        latency("proposed-dpki", "intra-off-chain"),
        latency("proposed-dpki", "intra-on-chain"),
        latency("proposed-dpki", "cross-on-chain"),
    ]
    lambda_p = float(pow_data["lambdaPerSec"].ravel()[0])
    mean_block_ms = float(pow_data["meanMs"].ravel()[0])

    rows = [
        [r"$\lambda$", "total request arrival rate", "controlled sweep"],
        [r"$p$", "management-request ratio", "controlled sweep"],
        [r"$\gamma$", "on-chain auth. ratio", "controlled sweep"],
        [r"$\varepsilon$", "cross-domain auth. ratio", "controlled sweep"],
        [r"$m$", "number of service CAs", "controlled sweep"],
        [r"$\mu$", "auth. service rate", f"{min(1000.0 / v for v in dpki_auth_ms):.1f}-{max(1000.0 / v for v in dpki_auth_ms):.1f} 1/s"],
        [r"$q\mu$", "management service rate", f"{1000.0 / dpki_mgmt_ms:.1f} 1/s"],
        [r"$\lambda_p$", "PoW block rate", f"{lambda_p:.2f} 1/s; difficulty tuned"],
    ]

    headers = ["Symbol", "Quantity in model", "Prototype/model input"]
    col_widths = np.array([0.15, 0.40, 0.45], dtype=float)

    savemat(
        DATA_FILE,
        {
            "headers": np.array(headers, dtype=object).reshape(-1, 1),
            "rows": np.array(rows, dtype=object),
            "colWidths": col_widths.reshape(-1, 1),
            "intervalsMs": pow_data["intervalsMs"],
            "xGridMs": pow_data["xGridMs"],
            "expPdf": pow_data["expPdf"],
            "sampleCount": pow_data["sampleCount"],
            "meanMs": pow_data["meanMs"],
            "cv": pow_data["cv"],
            "lambdaPerSec": pow_data["lambdaPerSec"],
        },
    )
    print(f"Saved {DATA_FILE}")


if __name__ == "__main__":
    main()
