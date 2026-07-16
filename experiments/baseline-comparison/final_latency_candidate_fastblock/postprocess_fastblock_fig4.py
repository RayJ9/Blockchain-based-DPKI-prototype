from pathlib import Path

import pandas as pd

from postprocess_pow_adjusted_fig4 import apply_flow_corrections, describe


ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT / "prototype_baseline_benchmark" / "outputs"
RAW_RUNS = [
    path for path in sorted(RUN_ROOT.glob("fastblock_1ms_2000_*"))
    if "flow_corrected" not in path.name
]
if not RAW_RUNS:
    raise FileNotFoundError("No raw fastblock_1ms_2000_* run found")
INPUT_DIR = RAW_RUNS[-1]
OUTPUT_DIR = RUN_ROOT / f"{INPUT_DIR.name}_flow_corrected"
AUTH_RECORD_CALIBRATION_RUNS = sorted(RUN_ROOT.glob("proposed_auth_interleaved_alt_1000_*"))
MANAGEMENT_ISSUE_CALIBRATION_RUNS = sorted(RUN_ROOT.glob("management_issue_calibration_1000_*"))

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
]


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


def add_full_contract_certificate_accounting(out: pd.DataFrame) -> None:
    """Make the full-contract baseline comparable to X.509-style workflows.

    The contract checks certificate records and status, but it does not parse or
    verify an X.509 certificate chain. For Fig4's stage-level comparison, add
    the same measured certificate/issuance processing used by the other
    baselines: one certificate for intra-domain authentication, two certificate
    checks for cross-domain authentication, and one issuance/update processing
    step for management.
    """
    for col in ["totalServiceMs", "issueUpdateMs", "certificateVerificationMs"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    pki_mgmt = out[
        (out["mechanism"] == "traditional-pki")
        & (out["requestClass"] == "management")
    ].set_index("index")
    pki_intra = out[
        (out["mechanism"] == "traditional-pki")
        & (out["requestClass"] == "intra-auth")
    ].set_index("index")

    mgmt_mask = (
        (out["mechanism"] == "full-contract-onchain")
        & (out["requestClass"] == "management")
    )
    mgmt_idx = out.loc[mgmt_mask, "index"]
    issue_extra = mgmt_idx.map(pki_mgmt["issueUpdateMs"]).fillna(pki_mgmt["issueUpdateMs"].mean()).to_numpy()
    out.loc[mgmt_mask, "issueUpdateMs"] += issue_extra
    out.loc[mgmt_mask, "totalServiceMs"] += issue_extra

    intra_mask = (
        (out["mechanism"] == "full-contract-onchain")
        & (out["requestClass"] == "intra-on-chain")
    )
    intra_idx = out.loc[intra_mask, "index"]
    cert_extra = intra_idx.map(pki_intra["certificateVerificationMs"]).fillna(pki_intra["certificateVerificationMs"].mean()).to_numpy()
    out.loc[intra_mask, "certificateVerificationMs"] += cert_extra
    out.loc[intra_mask, "totalServiceMs"] += cert_extra

    cross_mask = (
        (out["mechanism"] == "full-contract-onchain")
        & (out["requestClass"] == "cross-on-chain")
    )
    cross_idx = out.loc[cross_mask, "index"]
    cross_cert_extra = 2.0 * cross_idx.map(pki_intra["certificateVerificationMs"]).fillna(pki_intra["certificateVerificationMs"].mean()).to_numpy()
    out.loc[cross_mask, "certificateVerificationMs"] += cross_cert_extra
    out.loc[cross_mask, "totalServiceMs"] += cross_cert_extra


def apply_interleaved_auth_record_calibration(out: pd.DataFrame) -> Path:
    """Replace proposed putAuthRecord stages with interleaved measurements.

    The original fastblock run executes each request class in one large batch.
    For the proposed intra-domain and cross-domain on-chain workflows, the
    on-chain record operation is the same `putAuthRecord` call. Use the
    alternating interleaved calibration run so this shared stage is sampled under
    the same chain state without forcing the two request classes to be identical.
    """
    if not AUTH_RECORD_CALIBRATION_RUNS:
        raise FileNotFoundError("No proposed_auth_interleaved_alt_1000_* calibration run found")
    calibration_dir = AUTH_RECORD_CALIBRATION_RUNS[-1]
    calibration = pd.read_csv(calibration_dir / "request_metrics.csv")

    for col in ["totalServiceMs", "chainRecordMs", "receiptWaitMs"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    for request_class in ["intra-on-chain", "cross-on-chain"]:
        mask = (
            (out["mechanism"] == "proposed-dpki")
            & (out["requestClass"] == request_class)
        )
        source = calibration[
            (calibration["mechanism"] == "proposed-dpki")
            & (calibration["requestClass"] == request_class)
        ].sort_values("index")
        if source.empty:
            raise ValueError(f"No calibration rows for proposed-dpki/{request_class}")

        chain_values = pd.to_numeric(source["chainRecordMs"], errors="coerce").fillna(0.0).to_numpy()
        receipt_values = pd.to_numeric(source["receiptWaitMs"], errors="coerce").fillna(0.0).to_numpy()
        row_count = int(mask.sum())
        take = [idx % len(chain_values) for idx in range(row_count)]
        mapped_chain = chain_values[take]
        mapped_receipt = receipt_values[take]

        old_chain = out.loc[mask, "chainRecordMs"].to_numpy()
        old_receipt = out.loc[mask, "receiptWaitMs"].to_numpy()
        out.loc[mask, "chainRecordMs"] = mapped_chain
        out.loc[mask, "receiptWaitMs"] = mapped_receipt
        out.loc[mask, "totalServiceMs"] += mapped_chain - old_chain

    return calibration_dir


def apply_management_issue_accounting(out: pd.DataFrame) -> Path:
    """Use full certificate-issuance calibration for management requests.

    Management is a certificate issuance/update interaction. Replace the weak
    payload-signing proxy with a calibration that generates a CSR, signs an
    X.509 certificate, and writes a status/OCSP record. Management also has two
    signed message directions: CSR submission and certificate-result return, so
    add one more assertion stage to the already measured assertion.
    """
    if not MANAGEMENT_ISSUE_CALIBRATION_RUNS:
        raise FileNotFoundError("No management_issue_calibration_1000_* run found")
    calibration_dir = MANAGEMENT_ISSUE_CALIBRATION_RUNS[-1]
    calibration = pd.read_csv(calibration_dir / "request_metrics.csv").sort_values("index")
    issue_values = pd.to_numeric(calibration["issueUpdateMs"], errors="coerce").fillna(0.0).to_numpy()
    if len(issue_values) == 0:
        raise ValueError(f"No issueUpdateMs rows in {calibration_dir}")

    for col in ["totalServiceMs", "issueUpdateMs", "assertionMs"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    mask = out["requestClass"] == "management"
    row_count = int(mask.sum())
    take = [idx % len(issue_values) for idx in range(row_count)]
    mapped_issue = issue_values[take]

    old_issue = out.loc[mask, "issueUpdateMs"].to_numpy()
    extra_assertion = out.loc[mask, "assertionMs"].to_numpy()
    out.loc[mask, "issueUpdateMs"] = mapped_issue
    out.loc[mask, "assertionMs"] += extra_assertion
    out.loc[mask, "totalServiceMs"] += (mapped_issue - old_issue) + extra_assertion
    return calibration_dir


def add_full_contract_management_onchain_overhead(out: pd.DataFrame) -> None:
    """Account for full-contract certificate/status initialization.

    Full-contract management models certificate issuance and state initialization
    inside the contract. The raw contract write stores the certificate/root, but
    the figure should also include the certificate/status checking work that is
    moved on-chain by this baseline. Use the measured PKI intra-domain
    certificate + status validation stages as a conservative per-request
    equivalent and add it to the contract-execution stage.
    """
    for col in [
        "totalServiceMs",
        "contractExecutionMs",
        "certificateVerificationMs",
        "statusValidationMs",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    source = out[
        (out["mechanism"] == "traditional-pki")
        & (out["requestClass"] == "intra-auth")
    ].set_index("index")
    extra_source = source["certificateVerificationMs"] + source["statusValidationMs"]

    mask = (
        (out["mechanism"] == "full-contract-onchain")
        & (out["requestClass"] == "management")
    )
    idx = out.loc[mask, "index"]
    extra = idx.map(extra_source).fillna(extra_source.mean()).to_numpy()
    out.loc[mask, "contractExecutionMs"] += extra
    out.loc[mask, "totalServiceMs"] += extra


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = pd.read_csv(INPUT_DIR / "request_metrics.csv")
    corrected = rows.copy()
    apply_flow_corrections(corrected)
    add_full_contract_certificate_accounting(corrected)
    management_issue_dir = apply_management_issue_accounting(corrected)
    add_full_contract_management_onchain_overhead(corrected)
    calibration_dir = apply_interleaved_auth_record_calibration(corrected)
    corrected["notes"] = corrected.get("notes", "").fillna("").astype(str) + ";fastblock_flow_corrected_no_pow_deduction;full_contract_cert_accounting;management_full_issue_two_assertions;full_contract_management_onchain_overhead;proposed_putauthrecord_interleaved_calibration"
    corrected.to_csv(OUTPUT_DIR / "request_metrics.csv", index=False)
    summarize(corrected).to_csv(OUTPUT_DIR / "summary_by_request_class.csv", index=False)
    manifest = INPUT_DIR / "manifest.json"
    if manifest.exists():
        (OUTPUT_DIR / "manifest.source.json").write_text(manifest.read_text(encoding="utf-8"), encoding="utf-8")
    (OUTPUT_DIR / "manifest.json").write_text(
        "{\n"
        f'  "sourceRun": "{INPUT_DIR.as_posix()}",\n'
        f'  "authRecordCalibrationRun": "{calibration_dir.as_posix()}",\n'
        f'  "managementIssueCalibrationRun": "{management_issue_dir.as_posix()}",\n'
        '  "meanBlockMs": 1,\n'
        '  "note": "Flow-accounting corrections, full management issue calibration, full-contract management on-chain overhead, and alternating interleaved putAuthRecord calibration. No PoW/receipt waiting subtraction is applied."\n'
        "}\n",
        encoding="utf-8",
    )
    print(f"Input: {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
