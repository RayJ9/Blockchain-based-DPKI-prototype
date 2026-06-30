# Blockchain-Based DPKI Experiment Package

This repository keeps the prototype, experiment scripts, retained outputs, and
final paper figures for "Blockchain-Based Decentralized Public Key
Infrastructure Modeling and Analysis".

Final figure folders:

- `fig3`
- `fig4`
- `Fig5-lambda`
- `Fig6-epsilon`
- `Fig7-p`
- `Fig8-M`
- `fig9`
- `fig10`

Each folder contains the final `figure.*` outputs, retained data, and the
figure-generation scripts. Fig5-Fig8 also contain root-level `run_*.py` scripts
that rerun the corresponding prototype experiment through the restored Omnilink
PoW chain. `replot_figure.py` only redraws a figure from retained CSV data.

Main experiment components:

- `DPKI-and-DID-platform-Lenovo/chain33-dpki-real-experiment`: prototype
  experiment runner and smart contract.
- `DPKI-and-DID-platform-Lenovo/omnilink-pow-4nodes`: PoW four-node runtime
  scripts.
- `dpki-experiment-prototype`: compatibility copy of the prototype experiment
  directory used by older scripts.
- `pow-4nodes-runtime`: compatibility copy of the PoW runtime scripts used by
  older scripts.
- `omnilink`: restored Omnilink source tree.
- `simu2-8-packaged`: packaged queueing/availability experiment scripts.
- `simu2_tail_prob`: original simulation workspace retained for compatibility.

Typical full-experiment flow:

```powershell
python Fig5-lambda\run_fig5_lambda.py --requests 1000 --stop-pow
```

The Fig5-Fig8 `run_*.py` scripts restart the PoW chain by default. To manage the
chain manually, use `DPKI-and-DID-platform-Lenovo/omnilink-pow-4nodes/scripts`
and pass `--no-restart-pow` to the figure runner. The individual Fig5-Fig8
README files give the paper-scale commands and the retained-data replot
commands.

Private paper/editing folders are intentionally ignored by Git:

- `JIoT/`
- `response_letter/`
