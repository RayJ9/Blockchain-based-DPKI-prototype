from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


def _load_npz_surface(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    raw_lower = np.asarray(data["DPKI_LOWER"], dtype=float)
    raw_upper = np.asarray(data["DPKI_UPPER"], dtype=float)
    lower = np.minimum(raw_lower, raw_upper)
    upper = np.maximum(raw_lower, raw_upper)
    if "DPKI_MEAN" in data.files:
        raw_center = np.asarray(data["DPKI_MEAN"], dtype=float)
        center = np.minimum(np.maximum(raw_center, lower), upper)
    else:
        center = 0.5 * (lower + upper)
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


def _pick_four_indices(values: np.ndarray) -> np.ndarray:
    raw = np.linspace(0, len(values) - 1, 4)
    return np.unique(np.rint(raw).astype(int))


def _summary_rows(name: str, surface: dict[str, np.ndarray]) -> list[dict[str, float | str]]:
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


def main() -> None:
    current_dir = Path(__file__).resolve().parent
    source_dir = current_dir / "source_data"

    responding = _load_npz_surface(source_dir / "surface_data_matrices_responding.npz")
    malicious = _load_npz_surface(source_dir / "surface_data_matrices_malicious.npz")

    resp_indices = _pick_four_indices(responding["tsValues"])
    mal_indices = _pick_four_indices(malicious["tsValues"])

    mat = {}
    for prefix, surface in [("resp", responding), ("mal", malicious)]:
        for key, value in surface.items():
            export_key = key[:1].upper() + key[1:]
            mat[f"{prefix}{export_key}"] = value
    mat["respTsSliceIdx"] = (resp_indices + 1).astype(float)
    mat["malTsSliceIdx"] = (mal_indices + 1).astype(float)
    mat["respTsSliceValues"] = responding["tsValues"][resp_indices]
    mat["malTsSliceValues"] = malicious["tsValues"][mal_indices]

    savemat(current_dir / "data_fig9.mat", mat)

    summary = pd.DataFrame(
        _summary_rows("nodes_not_responding", responding)
        + _summary_rows("malicious_nodes", malicious)
    )
    summary.to_csv(current_dir / "figure_summary.csv", index=False)

    print("Saved fig9 data.")
    print(f"Responding t_s slices: {responding['tsValues'][resp_indices]}")
    print(f"Malicious t_s slices: {malicious['tsValues'][mal_indices]}")


if __name__ == "__main__":
    main()
