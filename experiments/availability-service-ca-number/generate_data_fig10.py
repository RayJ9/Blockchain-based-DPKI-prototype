from pathlib import Path
import sys

import pandas as pd
from scipy.io import savemat

CURRENT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = CURRENT_DIR.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from figure_dpki_pki_runtime.availability_common import (  # noqa: E402
    load_pf_m_csv,
    pick_four_indices,
    summary_rows,
)


def main() -> None:
    source_dir = CURRENT_DIR / "source_data"

    responding = load_pf_m_csv(source_dir / "availability_pf_m_slices_responding.csv", "nodes_not_responding")
    malicious = load_pf_m_csv(source_dir / "availability_pf_m_slices_malicious.csv", "malicious_nodes")

    resp_indices = pick_four_indices(responding["mValues"])
    mal_indices = pick_four_indices(malicious["mValues"])

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

    savemat(CURRENT_DIR / "data_fig10.mat", mat)
    summary = pd.DataFrame(
        summary_rows("nodes_not_responding", responding)
        + summary_rows("malicious_nodes", malicious)
    )
    summary.to_csv(CURRENT_DIR / "figure_summary.csv", index=False)

    print("Saved fig10 data.")
    print(f"Responding M slices: {responding['mValues'][resp_indices]}")
    print(f"Malicious M slices: {malicious['mValues'][mal_indices]}")


if __name__ == "__main__":
    main()
