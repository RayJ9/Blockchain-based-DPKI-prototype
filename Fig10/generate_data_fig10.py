from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


def _normalize_bounds(lower_raw: np.ndarray, upper_raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lower = np.minimum(lower_raw, upper_raw)
    upper = np.maximum(lower_raw, upper_raw)
    return lower, upper


def _load_pf_m_csv(path: Path, scenario: str) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
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

    pki = _pivot(df, "PKI", m_values, pf_values)
    lower_raw = _pivot(df, "DPKI_Lower", m_values, pf_values)
    upper_raw = _pivot(df, "DPKI_Upper", m_values, pf_values)
    lower, upper = _normalize_bounds(lower_raw, upper_raw)

    if "DPKI_Mean" in df.columns:
        center_raw = _pivot(df, "DPKI_Mean", m_values, pf_values)
        center = np.minimum(np.maximum(center_raw, lower), upper)
    else:
        center = 0.5 * (lower + upper)

    PF, M = np.meshgrid(pf_values, m_values)
    return {
        "scenario": scenario,
        "pfValues": pf_values,
        "mValues": m_values,
        "PF": PF,
        "M": M,
        "PKI": pki,
        "Lower": lower,
        "Upper": upper,
        "Center": center,
    }


def _pivot(df: pd.DataFrame, column: str, m_values: np.ndarray, pf_values: np.ndarray) -> np.ndarray:
    pivot = df.pivot_table(index="m", columns="pf", values=column, aggfunc="mean")
    pivot = pivot.reindex(index=m_values, columns=pf_values)
    if pivot.isna().any().any():
        raise ValueError(f"Missing values while pivoting {column}")
    return pivot.to_numpy(dtype=float)


def _pick_four_indices(values: np.ndarray) -> np.ndarray:
    raw = np.linspace(0, len(values) - 1, 4)
    return np.unique(np.rint(raw).astype(int))


def _summary_rows(surface: dict[str, np.ndarray]) -> list[dict[str, float | str]]:
    rows = []
    for label in ["PKI", "Lower", "Upper", "Center"]:
        values = surface[label]
        rows.append(
            {
                "scenario": surface["scenario"],
                "series": label,
                "min": float(np.nanmin(values)),
                "max": float(np.nanmax(values)),
                "mean": float(np.nanmean(values)),
            }
        )
    return rows


def main() -> None:
    current_dir = Path(__file__).resolve().parent
    source_dir = current_dir / "source_data"

    responding_csv = source_dir / "availability_pf_m_slices_responding.csv"
    malicious_csv = source_dir / "availability_pf_m_slices_malicious.csv"

    responding = _load_pf_m_csv(responding_csv, "nodes_not_responding")
    malicious = _load_pf_m_csv(malicious_csv, "malicious_nodes")

    resp_indices = _pick_four_indices(responding["mValues"])
    mal_indices = _pick_four_indices(malicious["mValues"])

    mat = {}
    for prefix, surface in [("resp", responding), ("mal", malicious)]:
        for key, value in surface.items():
            if key == "scenario":
                continue
            export_key = key[:1].upper() + key[1:]
            mat[f"{prefix}{export_key}"] = value
    mat["respMSliceIdx"] = (resp_indices + 1).astype(float)
    mat["malMSliceIdx"] = (mal_indices + 1).astype(float)
    mat["respMSliceValues"] = responding["mValues"][resp_indices]
    mat["malMSliceValues"] = malicious["mValues"][mal_indices]

    savemat(current_dir / "data_fig10.mat", mat)
    summary = pd.DataFrame(_summary_rows(responding) + _summary_rows(malicious))
    summary.to_csv(current_dir / "figure_summary.csv", index=False)

    print("Saved fig10 data.")
    print(f"Responding M slices: {responding['mValues'][resp_indices]}")
    print(f"Malicious M slices: {malicious['mValues'][mal_indices]}")


if __name__ == "__main__":
    main()
