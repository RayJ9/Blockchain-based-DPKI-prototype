import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from scipy.optimize import brentq


# ==============================================================================
# SECTION 1: LATENCY & QUEUEING HELPER FUNCTIONS
# ==============================================================================
def erlang_c_probability(m, rho):
    if m == 0: return 1.0
    if rho >= 1: return 1.0
    m_rho = m * rho
    try:
        m_int = int(m)
        sum_part = sum([(m_rho ** i) / math.factorial(i) for i in range(m_int)])
        numerator = (m_rho ** m_int) / math.factorial(m_int) * (1.0 / (1.0 - rho))
    except (ValueError, OverflowError):
        return 1.0
    denom = sum_part + numerator
    return numerator / denom if denom > 0 else 0.0


def get_mean_latency_pki(lambd, p, q, mu, m, epsilon, **kwargs):
    lam_per_server = lambd / m
    rho = (lam_per_server / mu) * (p / q + (1 - p))
    if rho >= 1: return float('inf')

    def pki_wait_time(lam, pr, qr, mur):
        stability_check = qr * mur - pr * lam - (1 - pr) * qr * lam
        if stability_check <= 0: return float('inf')
        num_Wq = (lam / (qr * mur)) * (pr + (1 - pr) * qr ** 2)
        return num_Wq / stability_check

    E_Wq = pki_wait_time(lam_per_server, p, q, mu)
    E_S = p / (q * mu) + (1 - p) / mu
    extra_delay = 3 * (1 - p) * epsilon * (1 / mu)
    return E_Wq + E_S + extra_delay


def get_mean_latency_dpki_lower(lambd, p, q, mu, m, gamma, epsilon, **kwargs):
    lambda_off = lambd * (1 - p) * (1 - gamma) * (1 - epsilon)
    rho_off = lambda_off / (m * mu) if m > 0 else float('inf')
    if rho_off >= 1: return float('inf')
    C = erlang_c_probability(m, rho_off)
    E_T_off = C / (m * mu * (1 - rho_off)) + 1 / mu if (1 - rho_off) > 0 and m > 0 else float('inf')
    lambda_on = lambd * (p + (1 - p) * gamma + (1 - p) * (1 - gamma) * epsilon)
    if lambda_on == 0:
        E_T_on = 0
    else:
        p_n = (p * lambd) / lambda_on

        def pki_wait_time(lam, pr, qr, mur):
            stability_check = qr * mur - pr * lam - (1 - pr) * qr * lam
            if stability_check <= 0: return float('inf')
            num_Wq = (lam / (qr * mur)) * (pr + (1 - pr) * qr ** 2)
            return num_Wq / stability_check

        E_Wq_on = pki_wait_time(lambda_on, p_n, q, mu)
        E_S_on = p_n / (q * mu) + (1 - p_n) / mu
        E_T_on = E_Wq_on + E_S_on
    w_on = lambda_on / lambd if lambd > 0 else 0
    w_off = lambda_off / lambd if lambd > 0 else 0
    return w_on * E_T_on + w_off * E_T_off


def get_mean_latency_dpki_upper(lambd, p, q, mu, m, gamma, lambda_p, epsilon, **kwargs):
    lambda_off = lambd * (1 - p) * (1 - gamma) * (1 - epsilon)
    rho_off = lambda_off / (m * mu) if m > 0 else float('inf')
    if rho_off >= 1: return float('inf')
    C = erlang_c_probability(m, rho_off)
    E_T_off = C / (m * mu * (1 - rho_off)) + 1 / mu if (1 - rho_off) > 0 and m > 0 else float('inf')
    lambda_on = lambd * (p + (1 - p) * gamma + (1 - p) * (1 - gamma) * epsilon)
    if lambda_on == 0:
        E_T_on = 0
    else:
        p_n = (p * lambd) / lambda_on
        rho_on_overall = lambda_on * (p_n / (q * mu) + (1 - p_n) / mu)
        if rho_on_overall >= 1: return float('inf')
        E_T_b1 = 1 / lambda_p
        E_B = lambda_on / lambda_p
        E_B2 = E_B ** 2 + E_B * (1 + lambda_on / lambda_p)
        E_Si = p_n / (q * mu) + (1 - p_n) / mu
        Var_Si = (p_n * 2 / ((q * mu) ** 2) + (1 - p_n) * 2 / (mu ** 2)) - E_Si ** 2
        E_S_block2 = E_B * Var_Si + E_B2 * (E_Si ** 2)
        rho_block_queue = lambda_p * E_B * E_Si
        if rho_block_queue >= 1: return float('inf')
        E_W_block = (lambda_p * E_S_block2) / (2 * (1 - rho_block_queue))
        E_S_req = E_Si * E_B2 / E_B if E_B > 0 else 0
        E_T_on = E_T_b1 + E_W_block + E_S_req
    w_on = lambda_on / lambd if lambd > 0 else 0
    w_off = lambda_off / lambd if lambd > 0 else 0
    return w_on * E_T_on + w_off * E_T_off


def get_tail_prob_M_M_m(ts, lambda_a, mu, m):
    if m <= 0: return 1.0
    rho = lambda_a / (m * mu)
    if rho >= 1: return 1.0
    C_m_rho = erlang_c_probability(m, rho)
    term1 = mu * (m - 1) - lambda_a
    if abs(term1) < 1e-9:
        prob = (C_m_rho * mu * ts + 1) * math.exp(-mu * ts)
    else:
        factor = (mu * C_m_rho) / term1
        term2 = 1 - math.exp(-term1 * ts)
        prob = math.exp(-mu * ts) + factor * term2
    return min(prob, 1.0)


def get_tail_prob_on_chain(ts, model_type, params):
    mean_latency_func = \
        {'pki': get_mean_latency_pki, 'dpki_lower': get_mean_latency_dpki_lower,
         'dpki_upper': get_mean_latency_dpki_upper}[
            model_type]
    E_T = mean_latency_func(**params)
    if E_T == float('inf') or E_T > 1e6: return 1.0
    if model_type == 'pki':
        lam = params['lambd'] / params['m'];
        pr = params['p']
    else:
        lam = params['lambd'] * (
                params['p'] + (1 - params['p']) * params['gamma'] + (1 - params['p']) * (1 - params['gamma']) *
                params['epsilon'])
        if lam == 0: return 0.0
        pr = (params['p'] * params['lambd']) / lam

    def lundberg_eq(eta, lam, pr, q, mu):
        if eta <= 0 or (q * mu - eta) <= 0 or (mu - eta) <= 0: return 1.0
        mgf = pr * (q * mu / (q * mu - eta)) + (1 - pr) * (mu / (mu - eta))
        return eta - lam * (mgf - 1)

    try:
        eta = brentq(lambda e: lundberg_eq(e, lam, pr, params['q'], params['mu']), 1e-9,
                     min(params['mu'], params['q'] * params['mu']) - 1e-9)
    except (ValueError, ZeroDivisionError):
        return 1.0
    alpha = eta * E_T;
    Ft = alpha * math.exp(-eta * ts)
    return min(Ft, 1.0)


# ==============================================================================
# SECTION 2: AVAILABILITY CALCULATION FUNCTIONS
# ==============================================================================
def binomial_prob(n, k, p):
    if k < 0 or k > n: return 0
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def calculate_availability_pki(pf, ts, params):
    Fi = min(pf + pf * (1 - pf) * (1 - params['p']) * params['epsilon'], 1.0)
    Ft = get_tail_prob_on_chain(ts, 'pki', params)
    return (1 - Fi) * (1 - Ft)


def calculate_availability_dpki_responding(pf, ts, params):
    bounds = {'lower': 0.0, 'upper': 0.0}
    total_m = params['m']
    lambda_a = params['lambd'] * (1 - params['p']) * (1 - params['gamma']) * (1 - params['epsilon'])
    lambda_b = params['lambd'] - lambda_a
    fail_prob_on_lower = (lambda_b / params['lambd']) * get_tail_prob_on_chain(ts, 'dpki_lower', params) if params[
                                                                                                                'lambd'] > 0 else 0
    fail_prob_on_upper = (lambda_b / params['lambd']) * get_tail_prob_on_chain(ts, 'dpki_upper', params) if params[
                                                                                                                'lambd'] > 0 else 0
    for k in range(total_m + 1):
        prob_k_servers = binomial_prob(total_m, k, 1 - pf)

        # <-- MODIFIED: Explicitly set availability to 0 when no servers are working (k=0)
        if k == 0:
            avail_k_lower = 0.0
            avail_k_upper = 0.0
        else:
            # Only calculate failure for k > 0
            fail_prob_off_given_k = (lambda_a / params['lambd']) * get_tail_prob_M_M_m(ts, lambda_a, params['mu'], k) if \
                params['lambd'] > 0 else 0
            avail_k_lower = 1 - fail_prob_off_given_k - fail_prob_on_lower
            avail_k_upper = 1 - fail_prob_off_given_k - fail_prob_on_upper

        bounds['lower'] += prob_k_servers * avail_k_lower
        bounds['upper'] += prob_k_servers * avail_k_upper

    return bounds['lower'], bounds['upper']


# ==============================================================================
# SECTION 3: MAIN PROGRAM & PLOTTING
# ==============================================================================
if __name__ == '__main__':
    # --- 1. Configuration ---
    M_VALUES_TO_TEST = [8,16,24]

    BASE_PARAMS = {
        'lambd': 3.0, 'p': 0.1, 'q': 0.3, 'mu': 7.5,
        'gamma': 0.3, 'epsilon': 0.1, 'lambda_p': 10
    }
    TIMEOUT_THRESHOLD_TS = 0.6
    pf_values = np.linspace(0, 1, 1000)

    print("--- Starting Availability Calculation for 'Nodes Not Responding' Scenario ---")
    print(f"Base parameters: {BASE_PARAMS}")
    print(f"M values to test: {M_VALUES_TO_TEST}")
    print(f"Timeout (ts): {TIMEOUT_THRESHOLD_TS}")

    # --- 2. Calculate theoretical availabilities for each m ---
    all_results = []
    for m_val in M_VALUES_TO_TEST:
        print(f"Calculating for m = {m_val}...")
        current_params = BASE_PARAMS.copy()
        current_params['m'] = m_val
        for pf in pf_values:
            avail_pki = calculate_availability_pki(pf, TIMEOUT_THRESHOLD_TS, current_params)
            resp_lower, resp_upper = calculate_availability_dpki_responding(pf, TIMEOUT_THRESHOLD_TS, current_params)
            all_results.append({
                'm': m_val, 'pf': pf, 'PKI': avail_pki,
                'DPKI_Lower': resp_lower, 'DPKI_Upper': resp_upper,
            })

    df = pd.DataFrame(all_results)
    output_filename = 'theoretical_availability_vs_pf_and_m.csv'
    df.to_csv(output_filename, index=False)
    print(f"Calculation complete. Data saved to: {output_filename}")

    # --- 3. Plotting ---
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 8))

    # Define color cycles for PKI and DPKI
    pki_colors = plt.get_cmap('Reds_r')(np.linspace(0.3, 0.9, len(M_VALUES_TO_TEST)))
    dpki_colors = plt.get_cmap('Blues_r')(np.linspace(0.3, 0.9, len(M_VALUES_TO_TEST)))

    for i, m_val in enumerate(M_VALUES_TO_TEST):
        m_df = df[df['m'] == m_val]

        # Plot PKI curve for the current m value
        plt.plot(m_df['pf'], m_df['PKI'],
                 label=f'PKI (m={m_val})',
                 linestyle='-', linewidth=2.5, color=pki_colors[i])

    for i, m_val in enumerate(M_VALUES_TO_TEST):
        m_df = df[df['m'] == m_val]

        # Plot DPKI curves (upper and lower bounds) for the current m value
        plt.plot(m_df['pf'], m_df['DPKI_Upper'],
                 linestyle='--', linewidth=2.0, color=dpki_colors[i])
        plt.plot(m_df['pf'], m_df['DPKI_Lower'],
                 linestyle=':', linewidth=2.0, color=dpki_colors[i])

        # Add a shaded region and a single legend entry for the DPKI range
        plt.fill_between(m_df['pf'], m_df['DPKI_Lower'], m_df['DPKI_Upper'],
                         color=dpki_colors[i], alpha=0.2, label=f'DPKI Range (m={m_val})')

    plt.title('Availability vs. Node Failure Probability (Nodes Not Responding)', fontsize=16)
    plt.xlabel('Node Failure Probability ($p_f$)', fontsize=14)
    plt.ylabel('System Availability $A(p_f)$', fontsize=14)

    # Create a clean, well-organized legend
    plt.legend(fontsize=12, title="System Configuration")

    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.xlim(0, 1)
    plt.ylim(0, 1.05)
    plt.xticks(np.arange(0, 1.1, 0.1), fontsize=12)
    plt.yticks(np.arange(0, 1.1, 0.1), fontsize=12)

    plt.tight_layout()
    plt.show()