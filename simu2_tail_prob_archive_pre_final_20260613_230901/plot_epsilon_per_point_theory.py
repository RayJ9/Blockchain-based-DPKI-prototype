from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
EXPERIMENT_OUT = WORKSPACE_ROOT / "DPKI-and-DID-platform-Lenovo" / "chain33-dpki-real-experiment" / "outputs"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from simu2_cross_domain_experiment import ModelParams, pki_theory_value  # noqa: E402
from simu3_compare_cross import (  # noqa: E402
    theoretical_values_dpki_lower_bound,
    theoretical_values_dpki_upper_bound,
)


def truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def stage_map(value: object) -> dict[str, float]:
    try:
        parsed = json.loads(value) if isinstance(value, str) and value else {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def stage_value_ms(stages: dict[str, float], key: str) -> float:
    try:
        return float(stages.get(key, 0.0))
    except Exception:
        return 0.0


def assertion_step_ms(stages: dict[str, float], assertion_prefix: str) -> float:
    return stage_value_ms(stages, f"{assertion_prefix}Sign") + stage_value_ms(stages, f"{assertion_prefix}Verify")


def cert_step_ms(stages: dict[str, float], verify_key: str, ocsp_prefix: str, assertion_prefix: str) -> float:
    return (
        stage_value_ms(stages, verify_key)
        + stage_value_ms(stages, f"{ocsp_prefix}OcspHttpQuery")
        + assertion_step_ms(stages, assertion_prefix)
    )


def finite_mean(values: list[float], fallback: float) -> float:
    clean = [float(value) for value in values if math.isfinite(float(value)) and float(value) > 0]
    return float(np.mean(clean)) if clean else float(fallback)


def fitted_curve(points: pd.DataFrame, x_col: str, y_col: str) -> tuple[np.ndarray, np.ndarray]:
    clean = points[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
    x = clean[x_col].to_numpy(dtype=float)
    y = clean[y_col].to_numpy(dtype=float)
    if len(clean) < 2:
        return x, y
    degree = min(3, len(clean) - 1)
    coeff = np.polyfit(x, y, degree)
    dense_x = np.linspace(float(np.min(x)), float(np.max(x)), 200)
    dense_y = np.polyval(coeff, dense_x)
    return dense_x, dense_y


def compute_per_epsilon_theory() -> pd.DataFrame:
    detailed = pd.read_csv(EXPERIMENT_OUT / "real_simulation_results_by_epsilon_detailed.csv")
    summary = pd.read_csv(EXPERIMENT_OUT / "real_summary_by_epsilon_detailed.csv")
    calibration = json.loads((EXPERIMENT_OUT / "real_calibrated_params.json").read_text(encoding="utf8"))

    detailed["onChainBool"] = truthy(detailed["onChain"])
    detailed["crossBool"] = truthy(detailed["crossDomain"])

    global_lambda_block = float(calibration["lambdaBlockMeasured"])
    service_cas = int(calibration["serviceCAs"])
    global_pki_extra_mu = float(calibration.get("pkiMuCrossExtraCertificateMeasured") or calibration["pkiMuPrimaryAuthMeasured"])
    global_pki_extra_sec = 1.0 / global_pki_extra_mu if global_pki_extra_mu > 0 else math.nan

    rows: list[dict[str, float]] = []
    dpki_summary = summary[summary["model"] == "DPKI"].copy()
    for _, summary_row in dpki_summary.sort_values("epsilon").iterrows():
        epsilon = float(summary_row["epsilon"])
        dpki = detailed[(detailed["model"] == "DPKI") & (detailed["epsilon"].astype(float) == epsilon)].copy()
        pki = detailed[(detailed["model"] == "PKI") & (detailed["epsilon"].astype(float) == epsilon)].copy()
        if dpki.empty or pki.empty:
            continue

        completed = float(len(dpki))
        arrival_span = float(summary_row.get("arrivalSpanSec", 0.0))
        lambda_total = completed / arrival_span if arrival_span > 0 else float(calibration["lambdaTotalMeasured"])
        p_manage = float((dpki["kind"] == "management").mean())

        normal_auth = dpki[dpki["kind"].isin(["intra-on-chain", "intra-off-chain"])]
        gamma = float((normal_auth["kind"] == "intra-on-chain").mean()) if len(normal_auth) else 0.0

        offchain_auth = dpki[dpki["kind"] == "intra-off-chain"]
        management = dpki[dpki["kind"] == "management"]
        mean_offchain_sec = finite_mean((offchain_auth["serviceMs"] / 1000.0).tolist(), 1.0 / float(calibration["muModelOffchainAuthMeasured"]))
        mean_management_sec = finite_mean((management["serviceMs"] / 1000.0).tolist(), float(calibration["meanManagementServiceSec"]))
        mu = 1.0 / mean_offchain_sec if mean_offchain_sec > 0 else math.nan
        q_manage = mean_offchain_sec / mean_management_sec if mean_management_sec > 0 else float(calibration["qManageMeasured"])

        pki_intra = pki[pki["kind"] == "intra-pki"]
        pki_mgmt = pki[pki["kind"] == "management"]
        pki_primary_sec = finite_mean((pki_intra["serviceMs"] / 1000.0).tolist(), float(calibration["pkiMeanPrimaryAuthServiceSec"]))
        pki_management_sec = finite_mean((pki_mgmt["serviceMs"] / 1000.0).tolist(), float(calibration["pkiMeanManagementServiceSec"]))
        pki_mu = 1.0 / pki_primary_sec if pki_primary_sec > 0 else float(calibration["pkiMuPrimaryAuthMeasured"])
        pki_q_manage = pki_primary_sec / pki_management_sec if pki_management_sec > 0 else float(calibration["pkiQManageMeasured"])

        cert_step_values_ms: list[float] = []
        for _, row in pki[pki["kind"] != "management"].iterrows():
            stages = stage_map(row.get("stageTimingsJson", ""))
            is_cross = bool(row.get("crossBool", False))
            leaf_assertion = "pkiLeafAssertion" if is_cross else "pkiOpenSslAssertion"
            cert_step_values_ms.append(cert_step_ms(stages, "pkiOpenSslVerifyLeaf", "pkiLeaf", leaf_assertion))
            if is_cross:
                cert_step_values_ms.append(
                    cert_step_ms(stages, "pkiOpenSslVerifySourceCA", "pkiSourceCA", "pkiSourceCAAssertion")
                )
                cert_step_values_ms.append(
                    cert_step_ms(stages, "pkiOpenSslVerifyRootCA", "pkiRootCA", "pkiRootCAAssertion")
                )
                cert_step_values_ms.append(
                    cert_step_ms(stages, "pkiOpenSslVerifyTargetCA", "pkiTargetCA", "pkiTargetCAAssertion")
                )
        pki_extra_sec = finite_mean([value / 1000.0 for value in cert_step_values_ms], global_pki_extra_sec)
        pki_extra_mu = 1.0 / pki_extra_sec if pki_extra_sec > 0 else global_pki_extra_mu

        upper = theoretical_values_dpki_upper_bound(
            lambda_total,
            p_manage,
            q_manage,
            mu,
            service_cas,
            gamma,
            global_lambda_block,
            epsilon,
        )
        lower = theoretical_values_dpki_lower_bound(
            lambda_total,
            p_manage,
            q_manage,
            mu,
            service_cas,
            gamma,
            global_lambda_block,
            epsilon,
        )
        pki_theory, pki_rho = pki_theory_value(
            ModelParams(
                lambda_total=lambda_total,
                p_manage=p_manage,
                q_manage=q_manage,
                mu=mu,
                service_cas=service_cas,
                gamma_on_chain=gamma,
                lambda_block=global_lambda_block,
                pki_mu=pki_mu,
                pki_q_manage=pki_q_manage,
                pki_cross_extra_mu=pki_extra_mu,
            ),
            epsilon,
        )

        rows.append(
            {
                "epsilon": epsilon,
                "DPKI_upper_theory_point": float(upper["E_T_total"]),
                "DPKI_lower_theory_point": float(lower["E_T_total"]),
                "PKI_theory_point": float(pki_theory),
                "PKI_rho": float(pki_rho),
                "DPKI_sim": float(summary_row["E_T"]),
                "PKI_sim": float(summary[(summary["model"] == "PKI") & (summary["epsilon"].astype(float) == epsilon)]["E_T"].iloc[0]),
                "lambdaTotalMeasuredPoint": lambda_total,
                "pManageMeasuredPoint": p_manage,
                "gammaMeasuredPoint": gamma,
                "qManageMeasuredPoint": q_manage,
                "muMeasuredPoint": mu,
                "pkiMuMeasuredPoint": pki_mu,
                "pkiQMeasuredPoint": pki_q_manage,
                "pkiCrossExtraMuMeasuredPoint": pki_extra_mu,
                "lambdaBlockMeasured": global_lambda_block,
                "serviceCAs": service_cas,
            }
        )

    return pd.DataFrame(rows).sort_values("epsilon")


def plot_per_point(points: pd.DataFrame) -> None:
    stem = "Fig7_epsilon_ET_noshape_r100_per_point_theory_fit"
    points.to_csv(SCRIPT_DIR / f"{stem}.csv", index=False)

    fig, ax = plt.subplots(figsize=(6.3, 4.2))
    for column, color, label, linestyle in [
        ("DPKI_upper_theory_point", (0.0, 0.5, 0.0), "DPKI Upper Fit", "--"),
        ("DPKI_lower_theory_point", (0.0, 0.447, 0.741), "DPKI Lower Fit", "--"),
        ("PKI_theory_point", (0.85, 0.0, 0.0), "PKI Theory Fit", "-"),
    ]:
        x_fit, y_fit = fitted_curve(points, "epsilon", column)
        ax.plot(x_fit, y_fit, linestyle, color=color, linewidth=1.5, label=label)
        clean = points[["epsilon", column]].replace([np.inf, -np.inf], np.nan).dropna()
        ax.plot(clean["epsilon"], clean[column], "o", color=color, markersize=3, alpha=0.65, label="_nolegend_")

    ax.plot(
        points["epsilon"],
        points["DPKI_sim"],
        "-o",
        color=(1.0, 0.4, 0.0),
        linewidth=1.8,
        markersize=4,
        label="DPKI Experimental",
    )
    ax.plot(
        points["epsilon"],
        points["PKI_sim"],
        "-o",
        color=(0.85, 0.0, 0.0),
        linewidth=1.8,
        markersize=4,
        label="PKI Experimental",
    )
    ax.set_xlabel(r"$\epsilon$")
    ax.set_ylabel(r"$E[T]$")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend(loc="best", fontsize=8, frameon=True)
    fig.tight_layout()
    fig.savefig(SCRIPT_DIR / f"{stem}.png", dpi=300)
    fig.savefig(SCRIPT_DIR / f"{stem}.eps", format="eps")
    plt.close(fig)


def main() -> None:
    points = compute_per_epsilon_theory()
    plot_per_point(points)
    print(points.to_string(index=False))


if __name__ == "__main__":
    main()
