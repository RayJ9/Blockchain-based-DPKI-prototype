from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMU = ROOT / "simu2_tail_prob"
LOG_PATH = SIMU / "final_5000_run.log"


def csv_range(start: int, stop: int, step: int = 1) -> str:
    return ",".join(str(value) for value in range(start, stop + 1, step))


def decimal_range(start: float, stop: float, step: float) -> str:
    values: list[str] = []
    value = start
    while value <= stop + 1e-9:
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        values.append(text)
        value += step
    return ",".join(values)


def figure_commands(reuse_existing: bool) -> list[tuple[str, list[str]]]:
    common_reuse = ["--reuse-existing"] if reuse_existing else []
    python = sys.executable
    return [
        (
            "Fig5-lambda",
            [
                python,
                str(SIMU / "Fig5-lambda" / "run_fig5_lambda.py"),
                "--lambda-values",
                csv_range(2, 16),
                "--mean-block-ms-values",
                "80,30,10",
                "--requests",
                "5000",
                "--epsilon",
                "0.1",
                "--p-manage",
                "0.1",
                "--gamma-on-chain",
                "0.1",
                "--q-manage",
                "0.3",
                "--service-cas",
                "4",
                "--tag",
                "final_r5000",
                "--stop-pow",
                *common_reuse,
            ],
        ),
        (
            "Fig6-epsilon",
            [
                python,
                str(SIMU / "Fig6-epsilon" / "run_fig6_epsilon.py"),
                "--epsilon-points",
                decimal_range(0.0, 0.6, 0.05),
                "--requests",
                "5000",
                "--lambda-arrival",
                "3",
                "--p-manage",
                "0.1",
                "--gamma-on-chain",
                "0.3",
                "--q-manage",
                "0.3",
                "--service-cas",
                "4",
                "--tag",
                "result",
                "--stop-pow",
            ],
        ),
        (
            "Fig7-p",
            [
                python,
                str(SIMU / "Fig7-p" / "run_fig7_p.py"),
                "--p-values",
                decimal_range(0.0, 0.7, 0.05),
                "--requests",
                "5000",
                "--lambda-arrival",
                "3",
                "--epsilon",
                "0.1",
                "--gamma-on-chain",
                "0.3",
                "--q-manage",
                "0.3",
                "--service-cas",
                "4",
                "--tag",
                "final_r5000_gamma0p3",
                "--stop-pow",
                *common_reuse,
            ],
        ),
        (
            "Fig8-M",
            [
                python,
                str(SIMU / "Fig8-M" / "run_fig8_m.py"),
                "--m-values",
                csv_range(2, 8),
                "--requests",
                "5000",
                "--lambda-arrival",
                "30",
                "--epsilon",
                "0.1",
                "--p-manage",
                "0.1",
                "--gamma-on-chain",
                "0.3",
                "--q-manage",
                "0.3",
                "--lambda-block",
                "30",
                "--tag",
                "final_r5000_lambda30_gamma0p3",
                "--stop-pow",
                *common_reuse,
            ],
        ),
    ]


def log(message: str) -> None:
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf8") as handle:
        handle.write(line + "\n")


def run_command(name: str, command: list[str], dry_run: bool) -> None:
    log(f"START {name}")
    log("COMMAND " + " ".join(f'"{part}"' if " " in part else part for part in command))
    if dry_run:
        log(f"DRY-RUN {name}")
        return
    started = time.perf_counter()
    subprocess.run(command, cwd=ROOT, check=True)
    elapsed = time.perf_counter() - started
    log(f"DONE {name} elapsed_seconds={elapsed:.1f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the final 5000-request figure suite.")
    parser.add_argument(
        "--start-at",
        choices=["Fig5-lambda", "Fig6-epsilon", "Fig7-p", "Fig8-M"],
        default="Fig5-lambda",
    )
    parser.add_argument("--only", choices=["Fig5-lambda", "Fig6-epsilon", "Fig7-p", "Fig8-M"], default="")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    commands = figure_commands(args.reuse_existing)
    if args.only:
        commands = [item for item in commands if item[0] == args.only]
    else:
        names = [name for name, _ in commands]
        start_index = names.index(args.start_at)
        commands = commands[start_index:]

    log("Final 5000-request run begins.")
    for name, command in commands:
        run_command(name, command, args.dry_run)
    log("Final 5000-request run finished.")


if __name__ == "__main__":
    main()
