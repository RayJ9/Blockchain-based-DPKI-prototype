# Final DPKI/PKI Figures

This folder now keeps only the final figure-generation code and the latest
1000-request result package.

Final outputs:

- `final_real_figures/Fig1_epsilon_ET.*`
- `final_real_figures/Fig2_lambda_ET.*`
- `final_real_figures/Fig3_p_ET.*`
- `final_real_figures/Fig4_M_ET.*`

Replot from the saved final CSV files:

```powershell
python simu2_tail_prob\replot_final_figures.py
```

Experiment runners:

- `run_final_first_three.py`: Fig1/Fig2/Fig3 real sweeps.
- `run_final_fig4_m.py`: Fig4 M-sweep runner using random thinning and exponential service shaping.
- `real_sweep_figures.py`: shared Chain33/DPKI/PKI experiment utilities.

Formula dependencies:

- `simu2_cross_domain_experiment.py`
- `simu3_compare_cross.py`
