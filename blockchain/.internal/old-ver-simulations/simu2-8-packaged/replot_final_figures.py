from __future__ import annotations

from pathlib import Path

import pandas as pd

from run_final_fig4_m import plot_fig4
from run_final_first_three import OUT_DIR, plot_fig1, plot_fig2, plot_fig3


def main() -> None:
    base = Path(OUT_DIR)
    plot_fig1(pd.read_csv(base / "Fig1_epsilon_ET_points.csv"))
    plot_fig2(pd.read_csv(base / "Fig2_lambda_ET_points.csv"))
    plot_fig3(pd.read_csv(base / "Fig3_p_ET_points.csv"))
    plot_fig4(pd.read_csv(base / "Fig4_M_ET_points.csv"))
    print(f"Replotted final figures under {base}")


if __name__ == "__main__":
    main()
