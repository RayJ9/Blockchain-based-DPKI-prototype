import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
import random
import pandas as pd

# === DPKI Model Parameters ===
# Users can replace these values with their actual parameters
# --------------------------------
lambda_total_dpki = 6  # Total request arrival rate λ
p_dpki = 0.1  # Proportion of management requests p
gamma_dpki = 0.1  # Proportion of high-security authentications γ
q_dpki = 0.1  # Ratio of management service rate to authentication service rate q
mu_dpki = 10  # Authentication service rate μ
lambda_p_dpki = 3  # Block generation rate λ_p
num_blocks_dpki = 10000000  # Number of blocks to simulate
episilon = 0.1
lambda_rate_mh21 = ((1 - p_dpki) * episilon + gamma_dpki * (1 - episilon) * (1 - p_dpki) + p_dpki) * lambda_total_dpki
# --------------------------------

# === M/H2/1 Model Parameters ===
# Users can replace these values with their actual parameters
# --------------------------------
# lambda_rate_mh21 = 3  # Arrival rate λ
mu1_mh21 = 1  # H2 service time first stage service rate μ₁
mu2_mh21 = 10  # H2 service time second stage service rate μ₂
p1_mh21 = 0.1  # H2 service time first stage probability p₁
p2_mh21 = 0.9  # H2 service time second stage probability p₂
num_customers_mh21 = 100000  # Number of customers to simulate
# --------------------------------


def run_dpki_model():
    """
    Executes the DPKI model simulation and analysis.
    Returns simulated and theoretical data for plotting.
    """
    print("=== DPKI Model Calculations (Bulk-Arrival Queue) ===")

    # --- parameters/aliases assumed defined globally:
    # p_dpki, episilon, gamma_dpki, lambda_total_dpki, lambda_p_dpki,
    # q_dpki, mu_dpki, num_blocks_dpki, np, fsolve

    # Effective normal-arrival rate and mixing prob.
    lambda_n = ((1 - p_dpki) * episilon + gamma_dpki * (1 - episilon) * (1 - p_dpki) + p_dpki) * lambda_total_dpki
    p_n = 0 if lambda_n == 0 else p_dpki / ((1 - p_dpki) * episilon + gamma_dpki * (1 - episilon) * (1 - p_dpki) + p_dpki)

    # Geometric PGF parameter for block size: p_B = λ_p / (λ_n + λ_p)
    if (lambda_n + lambda_p_dpki) == 0:
        p_B = 1.0
    else:
        p_B = lambda_p_dpki / (lambda_n + lambda_p_dpki)

    lambda_arrival_batch = lambda_p_dpki  # arrivals of blocks

    # Moments E[S], E[B], E[S_block]
    E_S = (p_n / (q_dpki * mu_dpki) + (1 - p_n) / mu_dpki)
    E_B = lambda_n / lambda_p_dpki if lambda_p_dpki > 0 else 0.0
    E_Sblock = E_B * E_S

    # Utilization check
    rho_block = lambda_arrival_batch * E_Sblock
    print(f"DPKI System Utilization (rho_block): {rho_block:.6f}")
    if rho_block >= 1:
        raise ValueError("The DPKI queue is unstable.")

    # Second moments
    E_S2 = 2 * (p_n / ((q_dpki * mu_dpki) ** 2) + (1 - p_n) / (mu_dpki ** 2))
    E_B2 = lambda_n * (2 * lambda_n + lambda_p_dpki) / (lambda_p_dpki ** 2) if lambda_p_dpki > 0 else 0.0
    Var_B = E_B2 - E_B ** 2
    E_Sblock2 = E_B * E_S2 + Var_B * (E_S ** 2)

    # === Solve the Lundberg root η from η = λ_p * ( G(M_S(η)) - 1 )  ===

    def MS(eta):
        # single-request MGF
        return p_n * (q_dpki * mu_dpki) / (q_dpki * mu_dpki - eta) + (1 - p_n) * (mu_dpki) / (mu_dpki - eta)

    def MS_prime(eta):
        # derivative of M_S(eta)
        return p_n * (q_dpki * mu_dpki) / (q_dpki * mu_dpki - eta) ** 2 + (1 - p_n) * (mu_dpki) / (mu_dpki - eta) ** 2

    def m1(eta):
        # block MGF = G(MS)
        return p_B / (1.0 - (1.0 - p_B) * MS(eta))

    def m1_prime(eta):
        # derivative via chain rule: G'(MS)*MS'
        denom = (1.0 - (1.0 - p_B) * MS(eta))
        return (p_B * (1.0 - p_B) * MS_prime(eta)) / (denom ** 2)

    def equation_for_eta_dpki(eta):
        # rearranged as eta - λ_p * ( m1(eta) - 1 ) = 0
        if np.isclose(eta, q_dpki * mu_dpki) or np.isclose(eta, mu_dpki):
            return 1e9
        return eta - lambda_arrival_batch * (m1(eta) - 1.0)

    min_service_rate = min(q_dpki * mu_dpki, mu_dpki)
    initial_guesses = np.linspace(1e-6, min_service_rate - 1e-6, 20)
    found_roots = []
    for guess in initial_guesses:
        try:
            root, infodict, ier, mesg = fsolve(equation_for_eta_dpki, guess, full_output=True)
            if ier == 1 and root[0] > 1e-6 and not any(np.isclose(root, r) for r in found_roots):
                found_roots.append(root[0])
        except RuntimeError:
            pass
    found_roots.sort()
    if not found_roots:
        raise ValueError("Could not find a non-trivial positive real root for eta (DPKI).")
    eta_val = found_roots[0]

    # === Exact residue constant α_T = ((1-ρ) η m1(η)) / (1 - λ_p m1'(η))  ===
    m1_eta = m1(eta_val)
    m1p_eta = m1_prime(eta_val)
    denom_alpha = 1.0 - lambda_arrival_batch * m1p_eta
    if np.isclose(denom_alpha, 0.0):
        raise ValueError("Denominator for exact alpha is numerically zero; parameters too close to singularity.")
    alpha_exact_tx = (1.0 - rho_block) * eta_val * m1_eta / denom_alpha

    # (Optional) keep the old rough constant for comparison
    EW_block = (lambda_arrival_batch * E_Sblock2) / (2.0 * (1.0 - rho_block))
    EW_tx = EW_block + E_Sblock
    alpha_approx_tx = eta_val * EW_block  # old heuristic (kept only for reference)

    print(f"Calculated DPKI Decay Rate (eta_val): {eta_val:.6f}")
    print(f"Calculated DPKI Asymptotic Constant (alpha_exact_tx): {alpha_exact_tx:.6f}  [EXACT]")
    print(f"Calculated DPKI Asymptotic Constant (alpha_approx_tx): {alpha_approx_tx:.6f}  [heuristic]")
    print(f"Theoretical Mean Total Delay (DPKI): {EW_tx:.6f}")

    # === Simulation (same as before) ===
    print("\n=== Simulating DPKI Second Stage (Transaction Level)... ===")
    arrival_times_batch = np.cumsum(np.random.exponential(1 / lambda_p_dpki, num_blocks_dpki))
    batch_sizes = np.random.geometric(p=p_B, size=num_blocks_dpki) - 1
    all_tx_sojourn_times = []
    departure_time_block = 0.0

    for i in range(num_blocks_dpki):
        batch_size = batch_sizes[i]
        arrival_time_block = arrival_times_batch[i]
        waiting_time_block = max(0.0, departure_time_block - arrival_time_block)
        start_service_time_block = arrival_time_block + waiting_time_block

        if batch_size > 0:
            N1 = np.random.binomial(n=batch_size, p=p_n)
            N2 = batch_size - N1
            S1_sum = np.sum(np.random.exponential(1 / (q_dpki * mu_dpki), N1)) if N1 > 0 else 0.0
            S2_sum = np.sum(np.random.exponential(1 / mu_dpki, N2)) if N2 > 0 else 0.0
            service_time_total_block = S1_sum + S2_sum
        else:
            service_time_total_block = 0.0

        total_tx_sojourn_time = waiting_time_block
        if batch_size > 0:
            for _ in range(batch_size):
                all_tx_sojourn_times.append(total_tx_sojourn_time)

        departure_time_block = start_service_time_block + service_time_total_block

    all_tx_sojourn_times_sim = np.array(all_tx_sojourn_times)
    print("=== Simulation Complete ===")
    print(f"Simulated Mean Total Delay: {np.mean(all_tx_sojourn_times_sim):.6f}")

    return {
        'sim_data': all_tx_sojourn_times_sim,
        'eta_val': eta_val,
        'alpha_exact': alpha_exact_tx,   # << 使用精确常数
        'alpha_approx': alpha_approx_tx, # 可选：保留旧估计作对照
        'E_S': E_S,
        'E_B': E_B,
        'E_Sblock': E_Sblock,
        'rho_block': rho_block,
        'E_S2': E_S2,
        'E_B2': E_B2,
        'E_Sblock2': E_Sblock2,
        'EW_block': EW_block,
        'EW_tx': EW_tx
    }



def run_mh21_model():
    """
    Executes the M/H2/1 model simulation and analysis, now for total time.
    Returns simulated and theoretical data for plotting.
    """
    print("\n=== M/H2/1 Model Calculations (Single-Arrival Queue) ===")
    if not np.isclose(p1_mh21 + p2_mh21, 1.0):
        print("Warning: p1 + p2 does not sum to 1.0.")

    E_V = p1_mh21 / mu1_mh21 + p2_mh21 / mu2_mh21
    E_V2 = 2 * (p1_mh21 / mu1_mh21 ** 2 + p2_mh21 / mu2_mh21 ** 2)
    rho = lambda_rate_mh21 * E_V
    print(f"M/H2/1 System Utilization (rho): {rho:.6f}")
    if rho >= 1:
        raise ValueError(f"The M/H2/1 queue is unstable.")

    def equation_for_eta_mh21(eta):
        return eta - lambda_rate_mh21 * (
                p1_mh21 * mu1_mh21 / (mu1_mh21 - eta) + p2_mh21 * mu2_mh21 / (mu2_mh21 - eta) - 1)

    initial_guesses = np.arange(0.1, min(mu1_mh21, mu2_mh21), 0.1)
    found_roots = []
    for guess in initial_guesses:
        try:
            root = fsolve(equation_for_eta_mh21, guess)
            if np.isreal(root) and root[0] > 1e-6 and not any(np.isclose(root, r) for r in found_roots):
                found_roots.append(root[0])
        except RuntimeError:
            pass
    found_roots.sort()
    if not found_roots:
        raise ValueError("Could not find a non-trivial positive real root for eta (M/H2/1).")
    eta_val = found_roots[0]

    EW = (lambda_rate_mh21 * E_V2) / (2 * (1 - rho))
    ET = EW + E_V  # New calculation for Expected Total Time
    alpha_approx = eta_val * EW  # Alpha is now based on ET
    print(f"Calculated M/H2/1 Decay Rate (eta_val): {eta_val:.6f}")
    print(f"Calculated M/H2/1 Asymptotic Constant (alpha_approx): {alpha_approx:.6f}")
    print(f"Theoretical Mean Total Delay (M/H2/1): {ET:.6f}")

    print("\n=== Simulating M/H2/1... ===")
    arrival_times = np.cumsum(np.random.exponential(1 / lambda_rate_mh21, num_customers_mh21))
    service_times = np.zeros(num_customers_mh21)
    for i in range(num_customers_mh21):
        if random.random() < p1_mh21:
            service_times[i] = np.random.exponential(1 / mu1_mh21)
        else:
            service_times[i] = np.random.exponential(1 / mu2_mh21)
    departure_time = 0
    sojourn_times = []  # Changed from waiting_times
    for i in range(num_customers_mh21):
        arrival_time = arrival_times[i]
        service_time = service_times[i]
        start_service_time = max(arrival_time, departure_time)
        departure_time = start_service_time + service_time
        sojourn_time = start_service_time - arrival_time  # Total time
        sojourn_times.append(sojourn_time)  # Appending total time
    sojourn_times_sim = np.array(sojourn_times)  # Changed from waiting_times_sim
    print("=== Simulation Complete ===")
    print(f"Simulated Mean Total Delay: {np.mean(sojourn_times_sim):.6f}")

    return {
        'sim_data': sojourn_times_sim,
        'eta_val': eta_val,
        'alpha_approx': alpha_approx,
        'E_V': E_V,
        'E_V2': E_V2,
        'rho': rho,
        'EW': EW,
        'ET': ET  # Add ET to the return dictionary
    }


def plot_results(dpki_results, mh21_results):
    """
    Plots the results from both models in a single figure.
    """
    plt.figure(figsize=(14, 9))

    # === Use the provided percentiles for both plots ===
    percentiles_for_comparison = np.arange(0, 100, 0.1)

    # --- DPKI Plotting ---
    x_at_percentile_dpki = np.percentile(dpki_results['sim_data'], percentiles_for_comparison)
    sim_tail_probs_dpki = (100 - percentiles_for_comparison) / 100.0
    x_approx_dpki = np.linspace(np.min(x_at_percentile_dpki), np.max(x_at_percentile_dpki), 500)
    y_approx_dpki = dpki_results['alpha_approx'] * np.exp(-dpki_results['eta_val'] * x_approx_dpki)

    plt.plot(x_at_percentile_dpki, sim_tail_probs_dpki, 'o', label='DPKI Simulated Data', color='blue', markersize=3)
    plt.plot(x_approx_dpki, y_approx_dpki, '--',
             label=f'DPKI Approx: ${dpki_results["alpha_approx"]:.4f}e^{{-{dpki_results["eta_val"]:.4f}x}}$',
             color='red')

    # --- M/H2/1 Plotting ---
    x_at_percentile_mh21 = np.percentile(mh21_results['sim_data'], percentiles_for_comparison)
    sim_tail_probs_mh21 = (100 - percentiles_for_comparison) / 100.0
    x_approx_mh21 = np.linspace(np.min(x_at_percentile_mh21), np.max(x_at_percentile_mh21), 500)
    y_approx_mh21 = mh21_results['alpha_approx'] * np.exp(-mh21_results['eta_val'] * x_approx_mh21)

    plt.plot(x_at_percentile_mh21, sim_tail_probs_mh21, 'x', label='M/H2/1 Simulated Data', color='green', markersize=4)
    plt.plot(x_approx_mh21, y_approx_mh21, ':',
             label=f'M/H2/1 Approx: ${mh21_results["alpha_approx"]:.4f}e^{{-{mh21_results["eta_val"]:.4f}x}}$',
             color='purple')

    # Update plot title
    plt.title('Tail Probability of Total Delay (DPKI) vs. Total Delay (M/H2/1)', fontsize=16)
    plt.xlabel('Time (x)', fontsize=12)
    plt.ylabel('Tail Probability P(T > x)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, which="both", ls="--", alpha=0.6)

    # Set x-axis limits to be tight
    all_x = np.concatenate((x_at_percentile_dpki, x_at_percentile_mh21))
    plt.xlim(np.min(all_x), np.max(all_x))
    plt.ylim(bottom=0)
    plt.show()


def save_results_to_csv(dpki_results, mh21_results, filename='simulation_results.csv'):
    """
    Saves the simulation and theoretical results to a CSV file.
    """
    dpki_sim_data = dpki_results['sim_data']
    mh21_sim_data = mh21_results['sim_data']

    percentiles = np.arange(0, 100, 0.1)

    # DPKI Results
    dpki_percentile_values = np.percentile(dpki_sim_data, percentiles)
    dpki_sim_tail_probs = (100 - percentiles) / 100.0
    dpki_approx_tail_probs = dpki_results['alpha_approx'] * np.exp(-dpki_results['eta_val'] * dpki_percentile_values)

    # M/H2/1 Results
    mh21_percentile_values = np.percentile(mh21_sim_data, percentiles)
    mh21_sim_tail_probs = (100 - percentiles) / 100.0
    mh21_approx_tail_probs = mh21_results['alpha_approx'] * np.exp(-mh21_results['eta_val'] * mh21_percentile_values)

    # Create a DataFrame
    df = pd.DataFrame({
        'Percentile': percentiles,
        'DPKI_Sim_Time_Value': dpki_percentile_values,
        'DPKI_Sim_Tail_Prob': dpki_sim_tail_probs,
        'DPKI_Approx_Tail_Prob': dpki_approx_tail_probs,
        'M/H2/1_Sim_Time_Value': mh21_percentile_values,
        'M/H2/1_Sim_Tail_Prob': mh21_sim_tail_probs,
        'M/H2/1_Approx_Tail_Prob': mh21_approx_tail_probs,
    })

    # Add a section for key theoretical values
    theoretical_data = {
        'Parameter': [
            'DPKI_lambda_n', 'DPKI_rho_block', 'DPKI_EW_tx', 'DPKI_eta_val', 'DPKI_alpha_approx',
            'M/H2/1_lambda_rate', 'M/H2/1_rho', 'M/H2/1_ET', 'M/H2/1_eta_val', 'M/H2/1_alpha_approx'
        ],
        'Value': [
            ((1 - p_dpki) * episilon + gamma_dpki * (1 - episilon) * (1 - p_dpki) + p_dpki) * lambda_total_dpki,
            dpki_results['rho_block'], dpki_results['EW_tx'], dpki_results['eta_val'], dpki_results['alpha_approx'],
            lambda_rate_mh21, mh21_results['rho'], mh21_results['ET'], mh21_results['eta_val'],
            mh21_results['alpha_approx']
        ]
    }
    df_theoretical = pd.DataFrame(theoretical_data)

    # Save to CSV
    with open(filename, 'w') as f:
        df_theoretical.to_csv(f, index=False)
        f.write('\n\n')  # Add some space
        df.to_csv(f, index=False)

    print(f"\nResults saved to {filename}")


def main():
    dpki_results = run_dpki_model()
    mh21_results = run_mh21_model()
    plot_results(dpki_results, mh21_results)
    save_results_to_csv(dpki_results, mh21_results, 'simulation_results.csv')


if __name__ == "__main__":
    main()