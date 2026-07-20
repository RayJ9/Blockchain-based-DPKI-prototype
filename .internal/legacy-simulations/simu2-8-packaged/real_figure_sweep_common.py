from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[2]
EPSILON_DIR = SCRIPT_DIR / "Fig6-epsilon"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(EPSILON_DIR) not in sys.path:
    sys.path.insert(0, str(EPSILON_DIR))

from real_sweep_figures import POW_RUNTIME, SWEEP_ROOT, RunSpec, run_real_experiment  # noqa: E402
import run_fig6_epsilon as epsilon_common  # noqa: E402

POW_SCRIPTS = WORKSPACE_ROOT / "blockchain" / "pow-4nodes-runtime" / "scripts"
FINAL_OUTPUT_FILES = [
    "figure.png",
    "figure.eps",
    "figure_data.csv",
    "delay_by_request_type.csv",
    "manifest.json",
]
LEGACY_PATTERNS = [
    "*_ET.png",
    "*_ET.eps",
    "*_ET_points.csv",
    "*_ET_smooth.csv",
    "*_ET_delay_by_kind.csv",
    "*_ET_bounds_check.csv",
    "*_ET_tx_health.csv",
    "manifest_*_ET.json",
]
PLOT_SERIES = [
    ("DPKI_upper_theory", "DPKI_upper_bound", "DPKI Upper Bound", "-", (0.0, 0.5, 0.0), True, None),
    ("DPKI_lower_theory", "DPKI_lower_bound", "DPKI Lower Bound", "-", (0.0, 0.447, 0.741), True, None),
    ("DPKI_sim", "DPKI_experimental", "DPKI Experimental Trend", "--", (1.0, 0.4, 0.0), True, "o"),
    ("PKI_theory", "PKI_theory", "PKI Theory", "-", (0.85, 0.0, 0.0), True, None),
    ("PKI_sim", "PKI_experimental", "PKI Experimental", "", (0.85, 0.0, 0.0), False, "D"),
]


def run_powershell(script: Path, args: list[str]) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
        cwd=WORKSPACE_ROOT,
        check=True,
    )


def restart_pow(mean_block_ms: int) -> None:
    run_powershell(POW_SCRIPTS / "stop-omnilink-pow-4nodes.ps1", [])
    ready = POW_RUNTIME / "ready.txt"
    if ready.exists():
        ready.unlink()
    run_powershell(
        POW_SCRIPTS / "start-omnilink-pow-4nodes.ps1",
        ["-MeanBlockMs", str(mean_block_ms), "-MineEmpty", "-AggregateMiningOnNode0", "-WarmupSeconds", "10"],
    )
    time.sleep(30)


def stop_pow() -> None:
    run_powershell(POW_SCRIPTS / "stop-omnilink-pow-4nodes.ps1", [])


def fmt_value(value: float | int) -> str:
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return str(value).replace(".", "p").replace("-", "m")


def parse_float_list(text: str) -> list[float]:
    values = [float(item.strip()) for item in text.split(",") if item.strip()]
    if not values:
        raise SystemExit("value list must contain at least one number")
    return values


def run_or_reuse(spec: RunSpec, reuse_existing: bool) -> Path:
    dest = SWEEP_ROOT / spec.sweep / spec.label
    detailed = dest / "real_simulation_results_by_epsilon_detailed.csv"
    calibration = dest / "real_calibrated_params.json"
    if reuse_existing and detailed.exists() and calibration.exists():
        return dest
    return run_real_experiment(spec)


def collect_sweep(
    specs: Iterable[tuple[float, RunSpec]],
    x_name: str,
    reuse_existing: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    point_rows: list[dict[str, object]] = []
    kind_frames: list[pd.DataFrame] = []
    tx_rows: list[dict[str, object]] = []

    for x_value, spec in specs:
        run_dir = run_or_reuse(spec, reuse_existing)
        points, by_kind = epsilon_common.build_points(
            run_dir,
            q_manage_override=spec.q_manage,
            dpki_q_mode=spec.dpki_q_mode,
            lambda_block_safety_factor=spec.lambda_block_safety_factor,
        )
        if len(points) != 1:
            raise RuntimeError(f"{run_dir} produced {len(points)} point rows; variable sweeps expect one epsilon")
        row = points.iloc[0].to_dict()
        row[x_name] = float(x_value)
        row["runDir"] = str(run_dir)
        point_rows.append(row)

        by_kind = by_kind.copy()
        by_kind[x_name] = float(x_value)
        by_kind["runDir"] = str(run_dir)
        kind_frames.append(by_kind)

        tx_path = run_dir / "real_chain_tx_breakdown.csv"
        if tx_path.exists():
            tx = pd.read_csv(tx_path)
            tx_rows.append(
                {
                    x_name: float(x_value),
                    "runDir": str(run_dir),
                    "txCount": int(len(tx)),
                    "maxSubmitToHashMs": float(pd.to_numeric(tx.get("submitToHashMs"), errors="coerce").max()),
                    "maxHashToReceiptMs": float(pd.to_numeric(tx.get("hashToReceiptMs"), errors="coerce").max()),
                    "maxTxTotalMs": float(pd.to_numeric(tx.get("totalMs"), errors="coerce").max()),
                    "maxSignMs": float(pd.to_numeric(tx.get("signMs"), errors="coerce").max()),
                    "maxNonceMs": float(pd.to_numeric(tx.get("nonceMs"), errors="coerce").max()),
                    "maxEstimateGasMs": float(pd.to_numeric(tx.get("estimateGasMs"), errors="coerce").max()),
                    "slowTxOver1000ms": int((pd.to_numeric(tx.get("totalMs"), errors="coerce") > 1000).sum()),
                    "slowSubmitOver1000ms": int((pd.to_numeric(tx.get("submitToHashMs"), errors="coerce") > 1000).sum()),
                }
            )

    points_df = pd.DataFrame(point_rows).sort_values(x_name)
    kinds_df = pd.concat(kind_frames, ignore_index=True) if kind_frames else pd.DataFrame()
    tx_df = pd.DataFrame(tx_rows).sort_values(x_name) if tx_rows else pd.DataFrame()
    return points_df, kinds_df, tx_df


def bounds_check(points: pd.DataFrame, x_name: str) -> pd.DataFrame:
    out = points.copy()
    out["DPKI_in_bounds"] = (
        (out["DPKI_sim"] >= out["DPKI_lower_theory"]) & (out["DPKI_sim"] <= out["DPKI_upper_theory"])
    )
    out["DPKI_minus_lower"] = out["DPKI_sim"] - out["DPKI_lower_theory"]
    out["DPKI_minus_upper"] = out["DPKI_sim"] - out["DPKI_upper_theory"]
    out["PKI_abs_error"] = (out["PKI_sim"] - out["PKI_theory"]).abs()
    out["PKI_signed_error"] = out["PKI_sim"] - out["PKI_theory"]
    return out.sort_values(x_name)


def whole_line_fit(x: np.ndarray, y: np.ndarray, dense_x: np.ndarray, degree: int = 3) -> np.ndarray:
    order = np.argsort(x)
    x = x[order].astype(float)
    y = y[order].astype(float)
    if len(x) == 1:
        return np.full_like(dense_x, y[0], dtype=float)
    fit_degree = min(degree, len(x) - 1)
    coefficients = np.polyfit(x, y, fit_degree)
    return np.polyval(coefficients, dense_x)


def cleanup_legacy_outputs(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in FINAL_OUTPUT_FILES:
        path = directory / name
        if path.exists():
            path.unlink()
    for pattern in LEGACY_PATTERNS:
        for path in directory.glob(pattern):
            if path.is_file():
                path.unlink()


def mirror_final_outputs(output_dir: Path, script_dir: Path) -> None:
    cleanup_legacy_outputs(script_dir)
    for name in FINAL_OUTPUT_FILES:
        source = output_dir / name
        if source.exists():
            shutil.copy2(source, script_dir / name)


def write_figure_data(points: pd.DataFrame, smooth: pd.DataFrame, x_name: str, output_dir: Path) -> None:
    rename_map = {source: clean for source, clean, *_ in PLOT_SERIES}
    raw = points.rename(columns=rename_map).copy()
    raw.insert(0, "dataKind", "measured_point")
    curve = smooth.rename(columns=rename_map).copy()
    curve.insert(0, "dataKind", "plot_curve")

    series_columns = [clean for _, clean, *_ in PLOT_SERIES]
    parameter_columns = [column for column in raw.columns if column not in {"dataKind", x_name, *series_columns}]
    for column in parameter_columns:
        if column not in curve.columns:
            curve[column] = np.nan
    columns = ["dataKind", x_name, *series_columns, *parameter_columns]
    pd.concat([raw[columns], curve[columns]], ignore_index=True).to_csv(output_dir / "figure_data.csv", index=False)


def plot_sweep(
    points: pd.DataFrame,
    x_name: str,
    output_dir: Path,
    prefix: str,
    xlabel: str,
    ylabel: str = r"$E[T]$ (s)",
    ylim: tuple[float, float] | None = None,
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = points.sort_values(x_name).replace([np.inf, -np.inf], np.nan)
    dense_x = np.linspace(float(frame[x_name].min()), float(frame[x_name].max()), 300)
    smooth = pd.DataFrame({x_name: dense_x})
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for column, _, label, style, color, show_line, marker in PLOT_SERIES:
        series_frame = frame[[x_name, column]].dropna()
        if series_frame.empty:
            continue
        x = series_frame[x_name].astype(float).to_numpy()
        y = series_frame[column].astype(float).to_numpy()
        if show_line:
            smooth[column] = whole_line_fit(x, y, dense_x)
            ax.plot(dense_x, smooth[column], style, color=color, linewidth=1.8, label=label)
        else:
            smooth[column] = np.nan
        if marker:
            point_label = "DPKI Experimental" if column == "DPKI_sim" else label
            ax.scatter(
                x,
                y,
                marker=marker,
                facecolors="none",
                edgecolors=color,
                linewidths=1.2,
                s=28 if marker == "o" else 32,
                label=point_label,
                zorder=3,
            )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(float(frame[x_name].min()), float(frame[x_name].max()))
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(loc="best", fontsize=8, frameon=True, framealpha=1.0)
    fig.tight_layout()
    fig.savefig(output_dir / "figure.png", dpi=300)
    fig.savefig(output_dir / "figure.eps", format="eps")
    plt.close(fig)
    write_figure_data(frame, smooth, x_name, output_dir)
    return smooth


def write_outputs(
    output_dir: Path,
    prefix: str,
    x_name: str,
    points: pd.DataFrame,
    by_kind: pd.DataFrame,
    tx_health: pd.DataFrame,
    args,
    extra_manifest: dict[str, object] | None = None,
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    cleanup_legacy_outputs(output_dir)
    logs_dir = output_dir / "logs"
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
    logs_dir.mkdir(parents=True)

    check = bounds_check(points, x_name)
    by_kind.to_csv(output_dir / "delay_by_request_type.csv", index=False)
    tx_health.to_csv(logs_dir / "tx_health.csv", index=False)
    check.to_csv(logs_dir / "bounds_check.csv", index=False)
    if "runDir" in points:
        run_columns = [column for column in ["runDir", x_name, "meanBlockMs", "configuredLambdaBlock"] if column in points]
        points[run_columns].to_csv(logs_dir / "run_sources.csv", index=False)
    manifest = {
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scriptArgs": vars(args) if hasattr(args, "__dict__") else {},
        "logsDir": str(logs_dir),
        "runs": points[["runDir", x_name]].to_dict(orient="records") if "runDir" in points else [],
        "checks": {
            "allDpkiInBounds": bool(check["DPKI_in_bounds"].all()) if len(check) else False,
            "maxPkiAbsError": float(check["PKI_abs_error"].max()) if len(check) else None,
            "maxTxTotalMs": float(tx_health["maxTxTotalMs"].max()) if len(tx_health) else None,
            "slowTxOver1000ms": int(tx_health["slowTxOver1000ms"].sum()) if len(tx_health) else None,
        },
    }
    if extra_manifest:
        manifest.update(extra_manifest)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    (logs_dir / "log_manifest.json").write_text(
        json.dumps(
            [
                {"savedAs": "bounds_check.csv", "description": "DPKI bound and PKI theory consistency check"},
                {"savedAs": "tx_health.csv", "description": "Per-sweep chain transaction health summary"},
                {"savedAs": "run_sources.csv", "description": "Raw experiment directories used for this figure"},
            ],
            indent=2,
        ),
        encoding="utf8",
    )
    return check
