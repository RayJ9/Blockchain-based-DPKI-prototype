from __future__ import annotations

from real_sweep_figures import BASE, RunSpec, run_real_experiment


if __name__ == "__main__":
    run_real_experiment(
        RunSpec(
            label="epsilon_lambdap30_extra_0p55_0p60",
            sweep="epsilon",
            x_name="epsilon",
            x_value=0.0,
            epsilon_points="0.55,0.6",
            requests=1000,
            lambda_arrival=BASE["lambda_arrival"],
            p_manage=BASE["p_manage"],
            gamma_on_chain=BASE["gamma_on_chain"],
            q_manage=BASE["q_manage"],
            service_cas=BASE["service_cas"],
            lambda_block=BASE["lambda_block"],
            offchain_shape_ms=BASE["offchain_shape_ms"],
            service_shape_mode=BASE["service_shape_mode"],
            seed=45600,
        )
    )
