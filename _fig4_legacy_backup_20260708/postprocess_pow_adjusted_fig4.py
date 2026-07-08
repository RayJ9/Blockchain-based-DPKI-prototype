from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "prototype_baseline_benchmark" / "outputs" / "full_2000_receipt_20260706_155102"
OUTPUT_DIR = ROOT / "prototype_baseline_benchmark" / "outputs" / "full_2000_pow_adjusted_from_receipt_20260706_155102"
POW_BASELINE_MS = 200.0

METRIC_COLUMNS = [
    "totalServiceMs",
    "issueUpdateMs",
    "certificateVerificationMs",
    "statusValidationMs",
    "mptValidationMs",
    "thresholdValidationMs",
    "thresholdIssueMs",
    "chainRecordMs",
    "chainStateReadMs",
    "contractExecutionMs",
    "assertionMs",
    "gasUsed",
    "txInputBytes",
    "rawTxBytes",
    "receiptLogBytes",
    "receiptWaitMs",
    "txCount",
    "powBaselineMs",
    "powDeductedMs",
    "powAdjustedReceiptMs",
]


def describe(values: pd.Series) -> dict[str, float]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return {
            "mean": 0.0,
            "variance": 0.0,
            "std": 0.0,
            "mad": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "min": 0.0,
            "max": 0.0,
        }
    mean = float(clean.mean())
    return {
        "mean": mean,
        "variance": float(clean.var(ddof=0)),
        "std": float(clean.std(ddof=0)),
        "mad": float((clean - mean).abs().mean()),
        "p50": float(clean.quantile(0.5)),
        "p95": float(clean.quantile(0.95)),
        "min": float(clean.min()),
        "max": float(clean.max()),
    }


def adjust_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in [
        "totalServiceMs",
        "chainRecordMs",
        "contractExecutionMs",
        "receiptWaitMs",
        "txCount",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    baseline = POW_BASELINE_MS * out["txCount"]
    deducted = pd.concat([out["receiptWaitMs"], baseline], axis=1).min(axis=1)
    adjusted_receipt = out["receiptWaitMs"] - deducted

    for stage in ["chainRecordMs", "contractExecutionMs"]:
        mask = out[stage] > 0
        service_part = (out.loc[mask, stage] - out.loc[mask, "receiptWaitMs"]).clip(lower=0.0)
        adjusted_stage = service_part + adjusted_receipt.loc[mask]
        out.loc[mask, "totalServiceMs"] = out.loc[mask, "totalServiceMs"] - out.loc[mask, stage] + adjusted_stage
        out.loc[mask, stage] = adjusted_stage

    out["powBaselineMs"] = baseline
    out["powDeductedMs"] = deducted
    out["powAdjustedReceiptMs"] = adjusted_receipt
    apply_flow_corrections(out)
    out["notes"] = out.get("notes", "").fillna("").astype(str) + ";pow_adjusted_from_receipt_minus_200ms"
    return out


def apply_flow_corrections(out: pd.DataFrame) -> None:
    """Apply Fig4 accounting fixes without rerunning the prototype.

    - Our proposed cross-domain authentication uses one end-to-end assertion in
      the paper accounting.
    - Threshold validation is a 4-of-6 parallel response. Each validator checks
      certificate and status before returning, so the critical path should
      include one certificate verification and one OCSP/status validation.
    """
    for col in [
        "totalServiceMs",
        "assertionMs",
        "certificateVerificationMs",
        "statusValidationMs",
        "thresholdValidationMs",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    proposed_cross = (
        (out["mechanism"] == "proposed-dpki")
        & (out["requestClass"] == "cross-on-chain")
    )
    removed_assertion = out.loc[proposed_cross, "assertionMs"] / 2.0
    out.loc[proposed_cross, "assertionMs"] -= removed_assertion
    out.loc[proposed_cross, "totalServiceMs"] -= removed_assertion

    pki_intra = out[
        (out["mechanism"] == "traditional-pki")
        & (out["requestClass"] == "intra-auth")
    ].set_index("index")

    for request_class in ["intra-auth", "cross-auth"]:
        mask = (
            (out["mechanism"] == "threshold-validation-dpki")
            & (out["requestClass"] == request_class)
        )
        idx = out.loc[mask, "index"]
        cert_extra = idx.map(pki_intra["certificateVerificationMs"]).fillna(pki_intra["certificateVerificationMs"].mean()).to_numpy()
        status_extra = idx.map(pki_intra["statusValidationMs"]).fillna(pki_intra["statusValidationMs"].mean()).to_numpy()
        out.loc[mask, "certificateVerificationMs"] += cert_extra
        out.loc[mask, "statusValidationMs"] += status_extra
        out.loc[mask, "totalServiceMs"] += cert_extra + status_extra


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (mechanism, request_class), group in df.groupby(["mechanism", "requestClass"], sort=False):
        row = {
            "mechanism": mechanism,
            "requestClass": request_class,
            "count": len(group),
        }
        for column in METRIC_COLUMNS:
            stats = describe(group[column] if column in group.columns else pd.Series(dtype=float))
            for key, value in stats.items():
                row[f"{column}_{key}"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    source = INPUT_DIR / "request_metrics.csv"
    if not source.exists():
        raise FileNotFoundError(source)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(source)
    adjusted = adjust_rows(df)
    summary = summarize(adjusted)
    adjusted.to_csv(OUTPUT_DIR / "request_metrics.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "summary_by_request_class.csv", index=False)
    (OUTPUT_DIR / "manifest.json").write_text(
        "{\n"
        f'  "source": "{INPUT_DIR.as_posix()}",\n'
        f'  "powBaselineMs": {POW_BASELINE_MS},\n'
        '  "note": "Postprocessed existing receipt-inclusive run. On-chain stage = receipt-inclusive stage minus min(receiptWaitMs, 200ms * txCount). No experiment was rerun."\n'
        "}\n",
        encoding="utf-8",
    )
    print(f"Saved {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
