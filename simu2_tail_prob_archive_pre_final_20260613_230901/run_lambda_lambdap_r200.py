from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from real_sweep_figures import (
    BASE,
    POW_RUNTIME,
    SCRIPT_DIR,
    SWEEP_ROOT,
    WORKSPACE_ROOT,
    RunSpec,
    fmt_value,
    read_run_point,
    run_real_experiment,
)
from simu2_cross_domain_experiment import ModelParams
from simu3_compare_cross import (
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)


SWEEP = "lambda_lambdap_r200"
LAMBDA_VALUES = [2, 3, 4, 5, 6, 7, 8]
MEAN_BLOCK_MS_VALUES = [20, 30, 40]
REQUESTS = 200
EPSILON = BASE["epsilon"]


def pow_script(name: str) -> Path:
    return (
        WORKSPACE_ROOT
        / "DPKI-and-DID-platform-Lenovo"
        / "omnilink-pow-4nodes"
        / "scripts"
        / name
    )


def run_powershell(script: Path, args: list[str]) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
        cwd=WORKSPACE_ROOT,
        check=True,
    )


def restart_pow(mean_block_ms: int) -> None:
    run_powershell(pow_script("stop-omnilink-pow-4nodes.ps1"), [])
    ready = POW_RUNTIME / "ready.txt"
    if ready.exists():
        ready.unlink()
    run_powershell(
        pow_script("start-omnilink-pow-4nodes.ps1"),
        ["-MeanBlockMs", str(mean_block_ms), "-MineEmpty", "-AggregateMiningOnNode0", "-WarmupSeconds", "10"],
    )
    time.sleep(30)


def run_point(mean_block_ms: int, lambda_arrival: float, seed: int) -> Path:
    label = f"lp_ms{mean_block_ms}_lambda_{fmt_value(lambda_arrival)}"
    run_dir = SWEEP_ROOT / SWEEP / label
    if (run_dir / "real_calibrated_params.json").exists() and (
        run_dir / "real_simulation_results_by_epsilon.csv"
    ).exists():
        print(f"skip existing {label}", flush=True)
        return run_dir

    print(f"run meanBlockMs={mean_block_ms} lambda={lambda_arrival}", flush=True)
    return run_real_experiment(
        RunSpec(
            label=label,
            sweep=SWEEP,
            x_name="lambda",
            x_value=float(lambda_arrival),
            epsilon_points=str(EPSILON),
            requests=REQUESTS,
            lambda_arrival=float(lambda_arrival),
            p_manage=BASE["p_manage"],
            gamma_on_chain=BASE["gamma_on_chain"],
            q_manage=BASE["q_manage"],
            service_cas=BASE["service_cas"],
            lambda_block=1000.0 / float(mean_block_ms),
            offchain_shape_ms=BASE["offchain_shape_ms"],
            service_shape_mode=BASE["service_shape_mode"],
            seed=seed,
            skip_pki=True,
        )
    )


def mean_finite(values: pd.Series, fallback: float) -> float:
    clean = pd.to_numeric(values, errors="coerce")
    clean = clean[np.isfinite(clean)]
    return float(clean.mean()) if len(clean) else fallback


def smooth_theory(group: pd.DataFrame, lambda_values: np.ndarray) -> pd.DataFrame:
    params = ModelParams(
        lambda_total=1.0,
        p_manage=mean_finite(group["pManageMeasured"], BASE["p_manage"]),
        q_manage=mean_finite(group["qManageMeasured"], BASE["q_manage"]),
        mu=mean_finite(group["muModelOffchainAuthMeasured"], 1.0 / 0.06),
        service_cas=int(round(mean_finite(group["serviceCAs"], BASE["service_cas"]))),
        gamma_on_chain=mean_finite(group["gammaOnChainMeasured"], BASE["gamma_on_chain"]),
        lambda_block=mean_finite(group["lambdaBlockMeasured"], BASE["lambda_block"]),
        pki_mu=mean_finite(group.get("pkiMuPrimaryAuthMeasured", pd.Series(dtype=float)), 1.0 / 0.06),
        pki_q_manage=mean_finite(group.get("pkiQManageMeasured", pd.Series(dtype=float)), BASE["q_manage"]),
        pki_cross_extra_mu=mean_finite(
            group.get("pkiMuCrossExtraCertificateMeasured", pd.Series(dtype=float)),
            1.0 / 0.06,
        ),
    )
    rows = []
    for value in lambda_values:
        upper = theoretical_values_dpki_upper_bound(
            value,
            params.p_manage,
            params.q_manage,
            params.mu,
            params.service_cas,
            params.gamma_on_chain,
            params.lambda_block,
            EPSILON,
        )["E_T_total"]
        lower = theoretical_values_dpki_lower_bound(
            value,
            params.p_manage,
            params.q_manage,
            params.mu,
            params.service_cas,
            params.gamma_on_chain,
            params.lambda_block,
            EPSILON,
        )["E_T_total"]
        rows.append(
            {
                "meanBlockMs": int(group["meanBlockMs"].iloc[0]),
                "lambda": float(value),
                "DPKI_upper_theory": float(upper),
                "DPKI_lower_theory": float(lower),
                "lambdaBlockMeasuredMean": params.lambda_block,
                "pManageMeasuredMean": params.p_manage,
                "gammaOnChainMeasuredMean": params.gamma_on_chain,
                "qManageMeasuredMean": params.q_manage,
                "muModelOffchainAuthMeasuredMean": params.mu,
                "serviceCAs": params.service_cas,
            }
        )
    return pd.DataFrame(rows)


def plot(points: pd.DataFrame, theory: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.1, 4.3))
    colors = {
        20: (0.0, 0.45, 0.74),
        30: (0.85, 0.33, 0.10),
        40: (0.47, 0.67, 0.19),
    }
    for mean_block_ms in MEAN_BLOCK_MS_VALUES:
        pts = points[points["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        curve = theory[theory["meanBlockMs"] == mean_block_ms].sort_values("lambda")
        if pts.empty or curve.empty:
            continue
        measured_lp = float(pts["lambdaBlockMeasured"].mean())
        label_prefix = rf"$\lambda_p\approx{measured_lp:.1f}/s$"
        color = colors.get(mean_block_ms)
        ax.plot(
            curve["lambda"],
            curve["DPKI_upper_theory"],
            "--",
            color=color,
            linewidth=1.4,
            label=f"{label_prefix} upper",
        )
        ax.plot(
            curve["lambda"],
            curve["DPKI_lower_theory"],
            ":",
            color=color,
            linewidth=1.4,
            label=f"{label_prefix} lower",
        )
        ax.plot(
            pts["lambda"],
            pts["DPKI_sim"],
            "-o",
            color=color,
            linewidth=1.6,
            markersize=4,
            label=f"{label_prefix} exp",
        )

    ax.set_xlabel(r"$\lambda$")
    ax.set_ylabel(r"$E[T]$")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=7, frameon=True)
    fig.tight_layout(rect=(0.0, 0.0, 0.78, 1.0))
    for out_dir in [SCRIPT_DIR, SWEEP_ROOT / SWEEP]:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_dir / "Fig_lambda_lambdap_r200.png", dpi=300)
        fig.savefig(out_dir / "Fig_lambda_lambdap_r200.eps", format="eps")
    plt.close(fig)


def main() -> None:
    all_rows: list[dict[str, float]] = []
    try:
        for mean_index, mean_block_ms in enumerate(MEAN_BLOCK_MS_VALUES):
            print(f"restart PoW meanBlockMs={mean_block_ms}", flush=True)
            restart_pow(mean_block_ms)
            for lambda_index, lambda_arrival in enumerate(LAMBDA_VALUES):
                seed = 52000 + mean_index * 1000 + lambda_index * 17
                run_dir = run_point(mean_block_ms, float(lambda_arrival), seed)
                row = read_run_point(run_dir, "lambda", float(lambda_arrival), EPSILON)
                calibration = json.loads((run_dir / "real_calibrated_params.json").read_text(encoding="utf8"))
                row.update(
                    {
                        "meanBlockMs": mean_block_ms,
                        "configuredLambdaBlock": 1000.0 / float(mean_block_ms),
                        "runDir": str(run_dir),
                        "lambdaBlockMeasurementSource": calibration.get("lambdaBlockMeasurementSource", ""),
                    }
                )
                all_rows.append(row)
                pd.DataFrame(all_rows).to_csv(SCRIPT_DIR / "Fig_lambda_lambdap_r200_points_partial.csv", index=False)
    finally:
        print("restore PoW meanBlockMs=20", flush=True)
        restart_pow(20)

    points = pd.DataFrame(all_rows).sort_values(["meanBlockMs", "lambda"])
    theory_frames = [
        smooth_theory(group, np.linspace(min(LAMBDA_VALUES), max(LAMBDA_VALUES), 121))
        for _, group in points.groupby("meanBlockMs")
    ]
    theory = pd.concat(theory_frames, ignore_index=True)
    out_dir = SWEEP_ROOT / SWEEP
    out_dir.mkdir(parents=True, exist_ok=True)
    points.to_csv(SCRIPT_DIR / "Fig_lambda_lambdap_r200_points.csv", index=False)
    theory.to_csv(SCRIPT_DIR / "Fig_lambda_lambdap_r200_theory_smooth.csv", index=False)
    points.to_csv(out_dir / "Fig_lambda_lambdap_r200_points.csv", index=False)
    theory.to_csv(out_dir / "Fig_lambda_lambdap_r200_theory_smooth.csv", index=False)
    plot(points, theory)
    print(points[["meanBlockMs", "lambda", "DPKI_sim", "lambdaBlockMeasured"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
