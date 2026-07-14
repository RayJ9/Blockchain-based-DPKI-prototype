from pathlib import Path
import sys

import pandas as pd
from scipy.io import savemat

CURRENT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = CURRENT_DIR.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from figure_dpki_pki_runtime.availability_common import (  # noqa: E402
    load_npz_surface,
    pick_four_indices,
    summary_rows,
)


def main() -> None:
    source_dir = CURRENT_DIR / "source_data"

    responding = load_npz_surface(source_dir / "surface_data_matrices_responding.npz")
    malicious = load_npz_surface(source_dir / "surface_data_matrices_malicious.npz")

    resp_indices = pick_four_indices(responding["tsValues"])
    mal_indices = pick_four_indices(malicious["tsValues"])

    mat = {}
    for prefix, surface in [("resp", responding), ("mal", malicious)]:
        for key, value in surface.items():
            export_key = key[:1].upper() + key[1:]
            mat[f"{prefix}{export_key}"] = value
    mat["respTsSliceIdx"] = (resp_indices + 1).astype(float)
    mat["malTsSliceIdx"] = (mal_indices + 1).astype(float)
    mat["respTsSliceValues"] = responding["tsValues"][resp_indices]
    mat["malTsSliceValues"] = malicious["tsValues"][mal_indices]

    savemat(CURRENT_DIR / "data_fig9.mat", mat)

    summary = pd.DataFrame(
        summary_rows("nodes_not_responding", responding)
        + summary_rows("malicious_nodes", malicious)
    )
    summary.to_csv(CURRENT_DIR / "figure_summary.csv", index=False)

    print("Saved fig9 data.")
    print(f"Responding t_s slices: {responding['tsValues'][resp_indices]}")
    print(f"Malicious t_s slices: {malicious['tsValues'][mal_indices]}")


if __name__ == "__main__":
    main()
