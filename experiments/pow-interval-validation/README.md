# PoW Interval Validation

Section VI.2 strict PoW-clock validation figure.

The figure uses the `poissonDelay` field emitted by the Omnilink
`PowNewBlock` log entry. This field is sampled by the exponential PoW clock
before transaction binding, block pre-execution, nonce scanning, block writes,
or RPC observation. It therefore matches the Poisson block-generation process
assumed by the analytical model.

- `source_data/strict_pow_clock_samples.csv`
- `source_data/strict_pow_clock_manifest.json`

The retained samples are calibrated to the target mean interval by a common
scale factor, equivalent to changing the PoW difficulty. This does not alter
the exponential distribution shape.

An isolated threshold-validation DPKI baseline prototype is provided under
`threshold_baseline/`. It writes separate CSV files and does not change this
figure unless its combined summary is explicitly used later.

Rebuild the figure data and redraw:

```powershell
python extract_strict_pow_clock.py
python generate_data_fig3.py
& 'C:\Program Files\MATLAB\R2024a\bin\matlab.exe' -batch "cd('experiments/pow-interval-validation'); plot_fig3"
```

Outputs:

- `figure.png`
- `figure.pdf`
- `figure.eps`

Kept data:

- `data_fig3.mat`
- `source_data/strict_pow_clock_samples.csv`
- `source_data/strict_pow_clock_manifest.json`
