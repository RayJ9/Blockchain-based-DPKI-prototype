import argparse
import csv
import json
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "outputs"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_openssl(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["openssl", *args],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def describe(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    mean = statistics.fmean(values) if values else 0.0
    return {
        "mean": mean,
        "variance": statistics.pvariance(values) if values else 0.0,
        "std": statistics.pstdev(values) if values else 0.0,
        "mad": statistics.fmean(abs(v - mean) for v in values) if values else 0.0,
        "p50": ordered[len(ordered) // 2] if values else 0.0,
        "p95": ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))] if values else 0.0,
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    out_dir = args.out or (OUTPUT_ROOT / f"management_issue_calibration_{args.requests}_{timestamp()}")
    work_dir = out_dir / "openssl_issue_work"
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    ca_key = work_dir / "ca.key"
    ca_cert = work_dir / "ca.crt"
    status_db = work_dir / "ocsp_status.csv"

    run_openssl(["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", str(ca_key)], work_dir)
    run_openssl(
        [
            "req",
            "-x509",
            "-new",
            "-key",
            str(ca_key),
            "-sha256",
            "-days",
            "3650",
            "-subj",
            "/CN=Fig4-CA",
            "-out",
            str(ca_cert),
        ],
        work_dir,
    )

    rows = []
    for i in range(max(1, args.requests)):
        leaf_key = work_dir / f"leaf_{i}.key"
        csr = work_dir / f"leaf_{i}.csr"
        cert = work_dir / f"leaf_{i}.crt"
        start = time.perf_counter()
        run_openssl(["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", str(leaf_key)], work_dir)
        run_openssl(["req", "-new", "-key", str(leaf_key), "-subj", f"/CN=Fig4-Leaf-{i}", "-out", str(csr)], work_dir)
        run_openssl(
            [
                "x509",
                "-req",
                "-in",
                str(csr),
                "-CA",
                str(ca_cert),
                "-CAkey",
                str(ca_key),
                "-set_serial",
                str(100000 + i),
                "-out",
                str(cert),
                "-days",
                "3650",
                "-sha256",
            ],
            work_dir,
        )
        with status_db.open("a", encoding="utf-8") as handle:
            handle.write(f"{i},valid,{int(time.time())}\n")
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        rows.append(
            {
                "index": i,
                "issueUpdateMs": elapsed_ms,
                "certBytes": cert.stat().st_size,
                "csrBytes": csr.stat().st_size,
                "statusBytes": len(f"{i},valid,{int(time.time())}\n".encode("utf-8")),
            }
        )

    with (out_dir / "request_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    stats = describe([row["issueUpdateMs"] for row in rows])
    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["count", *[f"issueUpdateMs_{k}" for k in stats]])
        writer.writeheader()
        writer.writerow({"count": len(rows), **{f"issueUpdateMs_{k}": v for k, v in stats.items()}})

    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "generatedAt": datetime.now().isoformat(),
                "requests": len(rows),
                "scope": "CSR generation, X.509 certificate signing, and OCSP/status record write",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Saved {out_dir}")


if __name__ == "__main__":
    main()
