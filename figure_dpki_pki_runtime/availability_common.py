from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def normalize_bounds(lower_raw: np.ndarray, upper_raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if not np.isfinite(lower_raw).all() or not np.isfinite(upper_raw).all():
        raise ValueError("Availability bounds contain non-finite values")
    if np.any(lower_raw > upper_raw):
        raise ValueError("Availability lower bound exceeds upper bound")
    return lower_raw, upper_raw


def pick_four_indices(values: np.ndarray) -> np.ndarray:
    raw = np.linspace(0, len(values) - 1, 4)
    return np.unique(np.rint(raw).astype(int))


def summary_rows(name: str, surface: dict[str, np.ndarray]) -> list[dict[str, float | str]]:
    rows = []
    for label in ["PKI", "Lower", "Upper", "Center"]:
        values = surface[label]
        rows.append(
            {
                "scenario": name,
                "series": label,
                "min": float(np.nanmin(values)),
                "max": float(np.nanmax(values)),
                "mean": float(np.nanmean(values)),
            }
        )
    return rows


def load_npz_surface(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as archive:
        data = {name: np.asarray(archive[name], dtype=float) for name in archive.files}
    raw_lower = np.asarray(data["DPKI_LOWER"], dtype=float)
    raw_upper = np.asarray(data["DPKI_UPPER"], dtype=float)
    lower, upper = normalize_bounds(raw_lower, raw_upper)
    if "DPKI_MEAN" in data:
        raw_center = np.asarray(data["DPKI_MEAN"], dtype=float)
        center = raw_center
    else:
        raise ValueError(f"{path} has no measured DPKI mean; no midpoint will be substituted")
    if center.shape != lower.shape or not np.isfinite(center).all():
        raise ValueError(f"{path} has invalid DPKI mean measurements")
    return {
        "PF": np.asarray(data["PF"], dtype=float),
        "TS": np.asarray(data["TS"], dtype=float),
        "PKI": np.asarray(data["PKI_AVAIL"], dtype=float),
        "Lower": lower,
        "Upper": upper,
        "Center": center,
        "pfValues": np.asarray(data["pf_values"], dtype=float).reshape(-1),
        "tsValues": np.asarray(data["ts_values"], dtype=float).reshape(-1),
    }


def pivot(df: pd.DataFrame, column: str, m_values: np.ndarray, pf_values: np.ndarray) -> np.ndarray:
    table = df.pivot(index="m", columns="pf", values=column)
    table = table.reindex(index=m_values, columns=pf_values)
    if not np.isfinite(table.to_numpy(dtype=float)).all():
        raise ValueError(f"Missing or non-finite values while pivoting {column}")
    return table.to_numpy(dtype=float)


def load_pf_m_csv(path: Path, scenario: str) -> dict[str, np.ndarray]:
    df = pd.read_csv(path, float_precision="round_trip")
    if "M" in df.columns:
        df = df.rename(columns={"M": "m"})
    if "PKI_Availability" in df.columns:
        df = df.rename(columns={"PKI_Availability": "PKI"})

    required = {"pf", "m", "PKI", "DPKI_Lower", "DPKI_Upper"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    pf_values = np.array(sorted(df["pf"].unique()), dtype=float)
    m_values = np.array(sorted(df["m"].unique()), dtype=float)

    pki = pivot(df, "PKI", m_values, pf_values)
    lower_raw = pivot(df, "DPKI_Lower", m_values, pf_values)
    upper_raw = pivot(df, "DPKI_Upper", m_values, pf_values)
    lower, upper = normalize_bounds(lower_raw, upper_raw)

    if "DPKI_Mean" in df.columns:
        center_raw = pivot(df, "DPKI_Mean", m_values, pf_values)
        center = center_raw
    else:
        raise ValueError(f"{path} has no measured DPKI mean; no midpoint will be substituted")

    pf_grid, m_grid = np.meshgrid(pf_values, m_values)
    return {
        "scenario": scenario,
        "pfValues": pf_values,
        "mValues": m_values,
        "PF": pf_grid,
        "M": m_grid,
        "PKI": pki,
        "Lower": lower,
        "Upper": upper,
        "Center": center,
    }
