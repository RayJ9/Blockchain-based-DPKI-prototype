import numpy as np
import pandas as pd
import math
import heapq
from collections import deque
import matplotlib.pyplot as plt
import random


# ------------------------------
# Queueing helpers (unchanged formulas; comments clarified)
# ------------------------------

def erlang_c_probability(m, rho_low):
    """
    Erlang-C probability P(wait) for M/M/m with offered load such that per-server utilization is rho_low.
    Here rho_low = lambda / (m*mu) by caller's definition.
    """
    if rho_low >= 1:
        return 1.0  # unstable; everyone waits

    # denominator = sum_{i=0}^{m-1} (m*rho)^i / i! + ((m*rho)^m / m!) * 1/(1-rho)
    # numerator   = ((m*rho)^m / m!) * 1/(1-rho)
    mr = m * rho_low
    # summation part
    sum_part = 0.0
    term = 1.0
    for i in range(m):
        if i > 0:
            term *= mr / i
        sum_part += term

    # numerator
    numerator = (mr ** m) / math.factorial(m) * (1.0 / (1.0 - rho_low))

    denom = sum_part + numerator
    if denom == 0.0:
        return 0.0
    return numerator / denom


def theoretical_values_dpki_upper_bound(lambd, p, q, mu, m, gamma, lambd_p, epsilon):
    """
    Upper bound model (three-stage). Logic preserved; only comments added.
    """
    rho_low = ((1 - p) * (1 - gamma) * (1 - epsilon) * lambd) / (m * mu)
    if rho_low >= 1:
        # print(f"警告: 低安全认证系统不稳定: rho_low = {rho_low:.5f} >= 1")
        return {
            'model': 'DPKI Upper Bound',
            'E_T_total': float('inf'),
            'E_T_stage1_upper': float('inf'),
            'E_T_stage2_upper': float('inf'),
            'E_T_stage3_upper': float('inf'),
            'rho_mg1_part': float('inf'),
            'rho_overall_system': float('inf')
        }

    C_m_rho_low = erlang_c_probability(m, rho_low)
    E_Wq_low = C_m_rho_low / (mu * m - (1 - p) * (1 - gamma) * (1 - epsilon) * lambd)
    E_S_low = 1 / mu
    E_T_low = E_Wq_low + E_S_low  # Stage 1 总时延

    lambd_n = (gamma * (1 - p) + p + (1 - p) * (1 - gamma) * epsilon) * lambd

    E_T_stage2_mempool = 1 / lambd_p

    if lambd_n == 0:
        p_n = 0.0
        E_B = 0.0
        E_B2 = 0.0
        E_Si_avg = 0.0
        Var_Si = 0.0
        E_S_batch = 0.0
        E_S_batch2 = 0.0
        rho = 0.0
        E_W_batch = 0.0
        E_B_tx_weighted = 0.0
        E_S_tx_weighted_theory = 0.0
        E_W_tx_weighted_theory = 0.0
    else:
        p_n = (p * lambd) / lambd_n

        # Geometric(block size) with mean E_B = lambd_n / lambd_p
        E_B = lambd_n / lambd_p
        Var_B = E_B + E_B ** 2
        E_B2 = Var_B + E_B ** 2

        # Per-transaction mean service time (mixture)
        E_Si_avg = (p_n / (q * mu) + (1 - p_n) / mu)

        # Batch service moments
        E_S_batch = E_B * E_Si_avg
        E_Si2_mgmt = 2 / (q * mu) ** 2
        E_Si2_auth = 2 / mu ** 2
        E_Si_sq_avg = p_n * E_Si2_mgmt + (1 - p_n) * E_Si2_auth
        Var_Si = E_Si_sq_avg - E_Si_avg ** 2
        E_S_batch2 = E_B * Var_Si + E_B2 * (E_Si_avg) ** 2

        rho = lambd_p * E_S_batch
        if rho >= 1:
            # print(f"警告: Stage 3 系统不稳定：rho = {rho:.5f} >= 1，请调整参数。")
            return {
                'model': 'DPKI Upper Bound',
                'E_T_total': float('inf'),
                'E_T_stage1_upper': float('inf'),
                'E_T_stage2_upper': float('inf'),
                'E_T_stage3_upper': float('inf'),
                'rho_mg1_part': float('inf'),
                'rho_overall_system': float('inf')
            }

        E_W_batch = (lambd_p * E_S_batch2) / (2 * (1 - rho)) if (1 - rho) > 0 else float('inf')

        E_B_tx_weighted = E_B2 / E_B if E_B > 0 else 0.0
        E_S_tx_weighted_theory = E_Si_avg * E_B_tx_weighted
        E_W_tx_weighted_theory = E_W_batch  # All tx share the batch wait

    E_T_stage3_upper = E_W_tx_weighted_theory + E_S_tx_weighted_theory

    E_T_total = ((1 - p) * gamma + p + (1 - p) * (1 - gamma) * epsilon) * \
                (E_T_stage2_mempool + E_T_stage3_upper) + \
                ((1 - p) * (1 - gamma) * (1 - epsilon) * E_T_low)

    return {
        'model': 'DPKI Upper Bound',
        'E_T_total': E_T_total,
        'E_T_stage1_upper': E_T_low,
        'E_T_stage2_upper': E_T_stage2_mempool,
        'E_T_stage3_upper': E_T_stage3_upper,
        'rho_mg1_part': rho,
        'rho_overall_system': np.nan
    }


def pki_lower_bound_eq9_ewq(lambd_n, p_n, q, mu):
    """
    [eq:PKI-9] lower bound for E[Wq] used in the DPKI lower-bound model.
    """
    stability_check = q * mu - p_n * lambd_n - (1 - p_n) * q * lambd_n
    if stability_check <= 0:
        return float('inf')

    numerator = (lambd_n / (q * mu)) * (p_n + (1 - p_n) * q ** 2)
    denominator = stability_check
    if denominator == 0:
        return float('inf')
    return numerator / denominator


def theoretical_values_dpki_lower_bound(lambd, p, q, mu, m, gamma, lambd_p, epsilon):
    """
    Lower bound model (three-stage). Logic preserved.
    """
    rho_low = ((1 - p) * (1 - gamma) * (1 - epsilon) * lambd) / (m * mu)
    if rho_low >= 1:
        return {
            'model': 'DPKI Lower Bound',
            'E_T_total': float('inf'),
            'E_T_stage1_lower': float('inf'),
            'E_T_stage2_lower': float('inf'),
            'E_T_stage3_lower': float('inf')
        }

    C_m_rho_low = erlang_c_probability(m, rho_low)
    E_Wq_low = C_m_rho_low / (mu * m * (1 - rho_low))
    E_S_low = 1 / mu
    E_T_low = E_Wq_low + E_S_low

    lambd_n = (gamma * (1 - p) + p + (1 - p) * (1 - gamma) * epsilon) * lambd

    E_T_stage2_mempool_lower = 0.0

    if lambd_n == 0:
        p_n = 0.0
        E_Si_lower = 0.0
        E_Wq_stage3_lower = 0.0
    else:
        p_n = (p * lambd) / lambd_n
        E_Si_lower = (p_n / (q * mu) + (1 - p_n) / mu)
        try:
            E_Wq_stage3_lower = pki_lower_bound_eq9_ewq(lambd_n, p_n, q, mu)
        except Exception:
            return {
                'model': 'DPKI Lower Bound',
                'E_T_total': float('inf'),
                'E_T_stage1_lower': float('inf'),
                'E_T_stage2_lower': float('inf'),
                'E_T_stage3_lower': float('inf')
            }

    E_T_stage3_lower = E_Wq_stage3_lower + E_Si_lower

    E_T_total_lower = ((1 - p) * gamma + p + (1 - p) * (1 - gamma) * epsilon) * \
                      (E_T_stage2_mempool_lower + E_T_stage3_lower) + \
                      ((1 - p) * (1 - gamma) * (1 - epsilon) * E_T_low)

    return {
        'model': 'DPKI Lower Bound',
        'E_T_total': E_T_total_lower,
        'E_T_stage1_lower': E_T_low,
        'E_T_stage2_lower': E_T_stage2_mempool_lower,
        'E_T_stage3_lower': E_T_stage3_lower
    }


# ------------------------------
# Memory-safe DPKI discrete-event simulator
# Online accumulation of stats to prevent memory overflow on long runs.
# ------------------------------

def run_simulation_dpki_model(lambd, p_mgmt, q, mu, m, gamma_from_low_sec, lambd_p,
                              T_end, T_warmup=0.0, epsilon=0.0):
    """
    Event-driven simulation with O(1) memory per completed request.
    We retain only:
      - queues of arrival timestamps (for low-level and mempool),
      - compact per-block records in the M/G/1 queue: (block_time, service_time, n, sum_initial_arrivals).
    All averages are accumulated online after passing warmup time.
    """
    sim_time = 0.0
    event_queue = []  # (time, event_type, payload)

    p = p_mgmt
    gamma = gamma_from_low_sec
    eps = epsilon

    # Splits of arrivals
    lambda_on_chain_total = (gamma * (1 - p) + p + (1 - p) * (1 - gamma) * eps) * lambd
    lambda_off_chain_total = (1 - p) * (1 - gamma) * (1 - eps) * lambd

    # schedule initial arrivals
    if lambda_on_chain_total > 0:
        heapq.heappush(event_queue,
                       (sim_time + np.random.exponential(1 / lambda_on_chain_total), 'arrival_on_chain', None))
    if lambda_off_chain_total > 0:
        heapq.heappush(event_queue,
                       (sim_time + np.random.exponential(1 / lambda_off_chain_total), 'arrival_off_chain', None))

    # Queues
    low_level_queue = deque()  # holds arrival_time (float)
    mempool_queue = deque()  # holds initial_arrival_time (float) == mempool_arrival_time for on-chain path
    on_chain_mg1_queue = deque()  # holds dict: {arrival_time, service_time, n, sum_initial_arrivals}

    # Low-level m servers
    low_level_servers = [{'busy_until': 0.0, 'req_arrival': None} for _ in range(m)]

    # M/G/1 "server": track next available time (finish time of current block)
    mg1_next_free_time = 0.0
    mg1_last_finish_time = 0.0  # for utilization metric compatible with old code

    # Schedule periodic block formation
    if lambd_p > 0:
        heapq.heappush(event_queue, (sim_time + random.expovariate(lambd_p), 'block_formation_event', None))

    # --- Online stats (post-warmup) ---
    s1_sum, s1_cnt = 0.0, 0
    s2_sum, s2_cnt = 0.0, 0
    s3_sum, s3_cnt = 0.0, 0
    total_sum, total_cnt = 0.0, 0
    completed_on_chain_cnt, completed_off_chain_cnt = 0, 0

    # AVOID MEMORY OVERFLOW: Check queue lengths
    QUEUE_LIMIT = 100000

    while event_queue and sim_time < T_end:
        # Check for queue overflow before processing
        if len(low_level_queue) > QUEUE_LIMIT or len(mempool_queue) > QUEUE_LIMIT or len(
                on_chain_mg1_queue) > QUEUE_LIMIT:
            print(
                f"警告: 仿真因队列过长而提前终止（内存保护）: low={len(low_level_queue)}, mp={len(mempool_queue)}, mg1={len(on_chain_mg1_queue)}")
            break

        event_time, event_type, payload = heapq.heappop(event_queue)
        sim_time = event_time

        # Arrivals
        if event_type == 'arrival_on_chain':
            mempool_queue.append(sim_time)
            if lambda_on_chain_total > 0:
                heapq.heappush(event_queue,
                               (sim_time + np.random.exponential(1 / lambda_on_chain_total), 'arrival_on_chain', None))
        elif event_type == 'arrival_off_chain':
            low_level_queue.append(sim_time)
            if lambda_off_chain_total > 0:
                heapq.heappush(event_queue, (
                sim_time + np.random.exponential(1 / lambda_off_chain_total), 'arrival_off_chain', None))

        # Service completion
        elif event_type == 'low_level_service_end':
            server_idx, arrival_time = payload['server_idx'], payload['arrival_time']
            finish_time = sim_time
            latency = finish_time - arrival_time
            if finish_time >= T_warmup:
                s1_sum += latency
                s1_cnt += 1
                total_sum += latency
                total_cnt += 1
                completed_off_chain_cnt += 1
            low_level_servers[server_idx]['busy_until'] = finish_time
            low_level_servers[server_idx]['req_arrival'] = None
        elif event_type == 'block_formation_event':
            block_time = sim_time
            n = len(mempool_queue)
            if n > 0:
                sum_arrivals = sum(mempool_queue)
                mempool_queue.clear()
                s2_sum += n * block_time - sum_arrivals
                s2_cnt += n
                total_block_service_time = 0.0
                prob_mgmt_on_chain = (p * lambd) / lambda_on_chain_total if lambda_on_chain_total > 0 else 0.0
                for _ in range(n):
                    total_block_service_time += random.expovariate(
                        q * mu) if random.random() < prob_mgmt_on_chain else random.expovariate(mu)
                on_chain_mg1_queue.append({'arrival_time': block_time, 'service_time': total_block_service_time, 'n': n,
                                           'sum_initial_arrivals': sum_arrivals})
            if lambd_p > 0:
                heapq.heappush(event_queue, (sim_time + random.expovariate(lambd_p), 'block_formation_event', None))
        elif event_type == 'mg1_service_end':
            blk = payload['block']
            finish_time = sim_time
            mg1_last_finish_time = finish_time
            n = blk['n']
            block_time = blk['arrival_time']
            s3_sum += n * (finish_time - block_time)
            s3_cnt += n
            total_sum += n * finish_time - blk['sum_initial_arrivals']
            total_cnt += n
            if finish_time >= T_warmup:
                completed_on_chain_cnt += n

        # Server pulls
        for i in range(m):
            if low_level_servers[i]['req_arrival'] is None and low_level_queue:
                arr_time = low_level_queue.popleft()
                service_time = random.expovariate(mu)
                end_time = sim_time + service_time
                low_level_servers[i]['busy_until'] = end_time
                low_level_servers[i]['req_arrival'] = arr_time
                heapq.heappush(event_queue,
                               (end_time, 'low_level_service_end', {'server_idx': i, 'arrival_time': arr_time}))
        if mg1_next_free_time <= sim_time and on_chain_mg1_queue:
            blk = on_chain_mg1_queue.popleft()
            start_time = max(blk['arrival_time'], sim_time, mg1_next_free_time)
            finish_time = start_time + blk['service_time']
            mg1_next_free_time = finish_time
            heapq.heappush(event_queue, (finish_time, 'mg1_service_end', {'block': blk}))

    mg1_sim_util = min(1.0,
                       (mg1_last_finish_time - T_warmup) / (sim_time - T_warmup)) if sim_time > T_warmup else np.nan
    E_T_stage1_sim = (s1_sum / s1_cnt) if s1_cnt > 0 else np.nan
    E_T_stage2_sim = (s2_sum / s2_cnt) if s2_cnt > 0 else np.nan
    E_T_stage3_sim = (s3_sum / s3_cnt) if s3_cnt > 0 else np.nan
    E_T_total_sim = (total_sum / total_cnt) if total_cnt > 0 else np.nan
    total_completed_after_warmup = completed_on_chain_cnt + completed_off_chain_cnt
    actual_P_on_chain = (
                completed_on_chain_cnt / total_completed_after_warmup) if total_completed_after_warmup > 0 else np.nan
    actual_P_off_chain = (
                completed_off_chain_cnt / total_completed_after_warmup) if total_completed_after_warmup > 0 else np.nan

    return {
        'model': 'DPKI Full Sim',
        'E_T_total': E_T_total_sim,
        'E_T_stage1_sim': E_T_stage1_sim,
        'E_T_stage2_sim': E_T_stage2_sim,
        'E_T_stage3_sim': E_T_stage3_sim,
        'rho_sim': mg1_sim_util,
        'actual_P_on_chain_sim': actual_P_on_chain,
        'actual_P_off_chain_sim': actual_P_off_chain
    }


# ------------------------------
# PKI (FCFS) theory & simulation (memory-safe)
# ------------------------------

def theory_fcfs_values(m, lambda_total, p_manage, mu_base, q_manage, epsilon):
    """
    Unchanged formula; returns (E_total_delay, rho).
    """
    lam = lambda_total / m
    p = p_manage
    mu = mu_base
    q = q_manage

    rho_pki_theory = (lam / mu) * (p / q + (1 - p))
    denominator_common_term = (1 - (p * lam / (q * mu)) - ((1 - p) * lam / mu))

    if denominator_common_term <= 0 or rho_pki_theory >= 1:
        return float('inf'), rho_pki_theory

    num_Wq_simplified = (lam / (q ** 2 * mu ** 2)) * (p + (1 - p) * q ** 2)
    theoretical_Wq_total = num_Wq_simplified / denominator_common_term

    E_S1 = 1 / (q * mu)
    E_S2 = 1 / mu
    E_S_avg = p * E_S1 + (1 - p) * E_S2 + 3 * (1 - p) * epsilon * E_S2

    theoretical_W_total = theoretical_Wq_total + E_S_avg
    return theoretical_W_total, rho_pki_theory


def simulate_fcfs_queue(m, lambd, p_manage, mu_base, q_manage,
                        sim_time, warmup_proportion, cooldown_proportion, epsilon):
    """
    Single-server FCFS with mixed service rates, simulated in O(1) memory.
    We compute filtered averages online when a job completes within [warmup, end-cooldown].
    """
    event_queue = []
    current_time = 0.0
    main_queue = deque()
    server_busy = False
    server_idle_time = 0.0
    last_event_time = 0.0
    lambda_total = lambd / m
    start_warmup_time_filter = sim_time * warmup_proportion
    end_cooldown_time_filter = sim_time * (1 - cooldown_proportion)
    filtered_sum_delay = 0.0
    filtered_cnt_delay = 0
    QUEUE_LIMIT = 100000

    heapq.heappush(event_queue, (random.expovariate(lambda_total), 0, None, None))

    while event_queue and current_time < sim_time:
        if len(main_queue) > QUEUE_LIMIT:
            print(f"警告: FCFS仿真因队列过长而提前终止（内存保护）: len={len(main_queue)}")
            break

        event_time, event_type, cust_arrival_to_system, cust_type_from_event = heapq.heappop(event_queue)

        if not server_busy and event_time > last_event_time:
            server_idle_time += (event_time - last_event_time)
        last_event_time = event_time
        current_time = event_time

        if event_type == 0:
            c_type = 1 if random.random() < p_manage else 2
            main_queue.append((current_time, c_type, current_time))
            heapq.heappush(event_queue, (current_time + random.expovariate(lambda_total), 0, None, None))
            if not server_busy and main_queue:
                arr_to_queue, ctype, original_arrival = main_queue.popleft()
                server_busy = True
                service_rate = (q_manage * mu_base) if ctype == 1 else mu_base
                service_time = random.expovariate(service_rate)
                heapq.heappush(event_queue, (current_time + service_time, 1, original_arrival, ctype))
        else:
            finish_time = current_time
            total_delay = finish_time - cust_arrival_to_system
            if cust_type_from_event == 2 and random.random() < epsilon:
                total_delay += (3 / mu_base)
            if start_warmup_time_filter <= finish_time <= end_cooldown_time_filter:
                filtered_sum_delay += total_delay
                filtered_cnt_delay += 1
            server_busy = False
            if main_queue:
                arr_to_queue, ctype, original_arrival = main_queue.popleft()
                server_busy = True
                service_rate = (q_manage * mu_base) if ctype == 1 else mu_base
                service_time = random.expovariate(service_rate)
                heapq.heappush(event_queue, (current_time + service_time, 1, original_arrival, ctype))

    avg_total_delay = (filtered_sum_delay / filtered_cnt_delay) if filtered_cnt_delay > 0 else np.nan
    sim_rho = (1 - (server_idle_time / current_time)) if current_time > 0 else np.nan
    return avg_total_delay, sim_rho


# ------------------------------
# Main (new memory management logic)
# ------------------------------

if __name__ == '__main__':
    # 固定其他参数，将p作为横轴变量
    # 进一步调整参数以使交点在p=0.3左右
    Q_MANAGE_SINGLE = 0.3   # 进一步增加管理队列服务率，提高DPKI性能
    MU_BASE_SINGLE = 8    # 进一步降低基础服务率，增加系统负载
    GAMMA_HIGH_SECURITY_SINGLE = 0.1   # 进一步降低高安全性参数
    LAMBDA_P_BLOCK_RATE_SINGLE = 35    # 进一步降低阻塞率参数

    SIM_TIME = 500000
    WARMUP_TIME = 10000

    WARMUP_PROPORTION = WARMUP_TIME / SIM_TIME
    COOLDOWN_PROPORTION = 0.1

    # Choose exactly one vector among the three below (others as scalars)
    # 现在将p作为横轴变量，其他参数固定
    DISCRETE_SIM_LAMBDA_VALUES = 2
    DISCRETE_SIM_M_VALUES = 4
    DISCRETE_SIM_EPSILON_VALUES = 0.1  # 固定epsilon值
    DISCRETE_SIM_P_VALUES = np.array([0.1, 0.15, 0.2, 0.25, 0.3,0.35,0.4])  # p作为横轴变量
    
    # --- x-axis resolution detection ---
    discrete_sim_x_values = []
    x_param_name = ''
    x_param_label = ''

    if isinstance(DISCRETE_SIM_LAMBDA_VALUES, (list, np.ndarray)):
        x_param_name = 'lambda'
        x_param_label = '$\\lambda$ (total arrival)'
        discrete_sim_x_values = DISCRETE_SIM_LAMBDA_VALUES
    elif isinstance(DISCRETE_SIM_M_VALUES, (list, np.ndarray)):
        x_param_name = 'M'
        x_param_label = 'M (low security servers)'
        discrete_sim_x_values = DISCRETE_SIM_M_VALUES
    elif isinstance(DISCRETE_SIM_EPSILON_VALUES, (list, np.ndarray)):
        x_param_name = 'epsilon'
        x_param_label = '$\\epsilon$'
        discrete_sim_x_values = DISCRETE_SIM_EPSILON_VALUES
    elif isinstance(DISCRETE_SIM_P_VALUES, (list, np.ndarray)):
        x_param_name = 'p'
        x_param_label = '$p$ (certificate management request ratio)'
        discrete_sim_x_values = DISCRETE_SIM_P_VALUES

    if not (isinstance(discrete_sim_x_values, (list, np.ndarray)) and len(discrete_sim_x_values) > 0):
        raise ValueError("没有检测到数组形式的横轴参数。请确保三者中只有一个是数组。")

    PLOT_X_MIN = np.min(discrete_sim_x_values)
    PLOT_X_MAX = np.max(discrete_sim_x_values)
    PLOT_NUM_POINTS = 100
    
    # 生成理论曲线的p值，避免与仿真点重复，但保留端点
    theory_x_values_raw = np.linspace(PLOT_X_MIN, PLOT_X_MAX, PLOT_NUM_POINTS)
    # 过滤掉与仿真点重复的p值（容差为0.001），但保留端点
    THEORY_X_VALUES_PLOT = []
    for theory_p in theory_x_values_raw:
        is_duplicate = False
        is_endpoint = (abs(theory_p - PLOT_X_MIN) < 1e-10) or (abs(theory_p - PLOT_X_MAX) < 1e-10)
        
        # 如果不是端点，则检查是否与仿真点重复
        if not is_endpoint:
            for sim_p in discrete_sim_x_values:
                if abs(theory_p - sim_p) < 0.001:
                    is_duplicate = True
                    break
        
        # 保留端点或非重复点
        if is_endpoint or not is_duplicate:
            THEORY_X_VALUES_PLOT.append(theory_p)
    THEORY_X_VALUES_PLOT = np.array(THEORY_X_VALUES_PLOT)

    print("--- 仿真参数设定 ---")
    print(f"横轴参数: {x_param_name} ({x_param_label})")
    print(
        f"固定 λ 值: {DISCRETE_SIM_LAMBDA_VALUES if not isinstance(DISCRETE_SIM_LAMBDA_VALUES, (list, np.ndarray)) else '随横轴变化'}")
    print(
        f"固定 M 值: {DISCRETE_SIM_M_VALUES if not isinstance(DISCRETE_SIM_M_VALUES, (list, np.ndarray)) else '随横轴变化'}")
    print(
        f"固定 epsilon 值: {DISCRETE_SIM_EPSILON_VALUES if not isinstance(DISCRETE_SIM_EPSILON_VALUES, (list, np.ndarray)) else '随横轴变化'}")
    print(f"证书管理请求比例 (p): {DISCRETE_SIM_P_VALUES if isinstance(DISCRETE_SIM_P_VALUES, (list, np.ndarray)) else '固定值'}")
    print(f"证书管理服务速率系数 (q): {Q_MANAGE_SINGLE}")
    print(f"基础服务率 (mu): {MU_BASE_SINGLE}")
    print(f"高安全认证请求比例 (gamma): {GAMMA_HIGH_SECURITY_SINGLE}")
    print(f"区块生成速率 (lambda_p): {LAMBDA_P_BLOCK_RATE_SINGLE}")
    print(f"仿真总时长: {SIM_TIME}")
    print(f"暖机时长: {WARMUP_TIME}")
    print(f"用于绘图的 {x_param_name} 范围: [{PLOT_X_MIN}, {PLOT_X_MAX}] ({PLOT_NUM_POINTS} 点)")
    print(f"用于离散仿真的 {x_param_name} 值: {discrete_sim_x_values}")
    print("-" * 30)

    # Stores all results for a final DataFrame
    all_results = []

    # Calculate and store all theory values
    print("--- 正在计算理论模型数据 ---")
    for current_x_val in THEORY_X_VALUES_PLOT:
        lambda_val_current = current_x_val if x_param_name == 'lambda' else DISCRETE_SIM_LAMBDA_VALUES
        m_val_current = int(current_x_val) if x_param_name == 'M' else DISCRETE_SIM_M_VALUES
        epsilon_val_current = current_x_val if x_param_name == 'epsilon' else DISCRETE_SIM_EPSILON_VALUES

        p_val_current = current_x_val if x_param_name == 'p' else 0.1  # 默认p值
        fcfs_w_total, _ = theory_fcfs_values(m_val_current, lambda_val_current, p_val_current, MU_BASE_SINGLE,
                                             Q_MANAGE_SINGLE, epsilon_val_current)
        dpki_upper_theory_res = theoretical_values_dpki_upper_bound(lambda_val_current, p_val_current,
                                                                    Q_MANAGE_SINGLE, MU_BASE_SINGLE, m_val_current,
                                                                    GAMMA_HIGH_SECURITY_SINGLE,
                                                                    LAMBDA_P_BLOCK_RATE_SINGLE, epsilon_val_current)
        dpki_lower_theory_res = theoretical_values_dpki_lower_bound(lambda_val_current, p_val_current,
                                                                    Q_MANAGE_SINGLE, MU_BASE_SINGLE, m_val_current,
                                                                    GAMMA_HIGH_SECURITY_SINGLE,
                                                                    LAMBDA_P_BLOCK_RATE_SINGLE, epsilon_val_current)

        all_results.append(
            {x_param_name: current_x_val, 'source': 'Theory', 'model': 'PKI FCFS', 'E_T_total': fcfs_w_total})
        all_results.append({x_param_name: current_x_val, 'source': 'Theory', 'model': 'DPKI Upper',
                            'E_T_total': dpki_upper_theory_res['E_T_total']})
        all_results.append({x_param_name: current_x_val, 'source': 'Theory', 'model': 'DPKI Lower',
                            'E_T_total': dpki_lower_theory_res['E_T_total']})
    print("理论数据计算完成。")

    # Run and store all simulation values, one by one
    for current_x_val in discrete_sim_x_values:
        lambda_val_current = current_x_val if x_param_name == 'lambda' else DISCRETE_SIM_LAMBDA_VALUES
        m_val_current = int(current_x_val) if x_param_name == 'M' else DISCRETE_SIM_M_VALUES
        epsilon_val_current = current_x_val if x_param_name == 'epsilon' else DISCRETE_SIM_EPSILON_VALUES
        p_val_current = current_x_val if x_param_name == 'p' else 0.1  # 默认p值

        print(f"\n--- 正在运行 {x_param_name} = {current_x_val} 的仿真 ---")

        # PKI / FCFS 对比模型仿真
        try:
            sim_W_total_fcfs, sim_rho_fcfs = simulate_fcfs_queue(m_val_current, lambda_val_current, p_val_current,
                                                                 MU_BASE_SINGLE, Q_MANAGE_SINGLE, SIM_TIME,
                                                                 WARMUP_PROPORTION, COOLDOWN_PROPORTION,
                                                                 epsilon_val_current)
            all_results.append({x_param_name: current_x_val, 'source': 'Simulation', 'model': 'PKI FCFS',
                                'E_T_total': sim_W_total_fcfs})
            print(f"PKI / FCFS 对比模型 仿真 E_total: {sim_W_total_fcfs:.5f}, ρ: {sim_rho_fcfs:.5f}")
        except Exception as e:
            print(f"PKI / FCFS 对比模型 仿真失败: {e}")
            all_results.append(
                {x_param_name: current_x_val, 'source': 'Simulation', 'model': 'PKI FCFS', 'E_T_total': np.nan})

        # DPKI 真实情况仿真
        try:
            dpki_sim_res = run_simulation_dpki_model(lambda_val_current, p_val_current, Q_MANAGE_SINGLE,
                                                     MU_BASE_SINGLE, m_val_current, GAMMA_HIGH_SECURITY_SINGLE,
                                                     LAMBDA_P_BLOCK_RATE_SINGLE, SIM_TIME, WARMUP_TIME,
                                                     epsilon_val_current)
            all_results.append({x_param_name: current_x_val, 'source': 'Simulation', 'model': 'DPKI Real',
                                'E_T_total': dpki_sim_res['E_T_total']})
            print(f"DPKI 真实情况仿真 E_total: {dpki_sim_res['E_T_total']:.5f}, ρ: {dpki_sim_res['rho_sim']:.5f}")
        except Exception as e:
            print(f"DPKI 真实情况仿真失败: {e}")
            all_results.append(
                {x_param_name: current_x_val, 'source': 'Simulation', 'model': 'DPKI Real', 'E_T_total': np.nan})

    # Create and save the final DataFrame to a CSV file
    final_df = pd.DataFrame(all_results)
    output_filename = 'simulation_results.csv'
    final_df.to_csv(output_filename, index=False)
    print(f"\n所有仿真和理论数据已保存到文件：{output_filename}")


    # 创建分离的数据存储结构
    # 1. 理论曲线数据（连续的p值）
    theory_df = final_df[final_df['source'] == 'Theory'].copy()
    theory_pivot = theory_df.pivot(index=x_param_name, columns='model', values='E_T_total')
    theory_pivot.columns = ['DPKI_lower_theory', 'DPKI_upper_theory', 'PKI_theory']
    theory_pivot = theory_pivot.reindex(columns=['DPKI_upper_theory', 'DPKI_lower_theory', 'PKI_theory'])
    
    # 2. 仿真数据（离散的p值）
    sim_df = final_df[final_df['source'] == 'Simulation'].copy()
    sim_pivot = sim_df.pivot(index=x_param_name, columns='model', values='E_T_total')
    sim_pivot.columns = ['DPKI_sim', 'PKI_sim']
    sim_pivot = sim_pivot.reindex(columns=['DPKI_sim', 'PKI_sim'])
    
    # 保存理论数据
    theory_filename = f'theory_results_by_{x_param_name}.csv'
    theory_pivot.to_csv(theory_filename)
    print(f"理论数据已保存到文件：{theory_filename}")
    
    # 保存仿真数据
    sim_filename = f'simulation_results_by_{x_param_name}.csv'
    sim_pivot.to_csv(sim_filename)
    print(f"仿真数据已保存到文件：{sim_filename}")
    
    # 为了兼容性，也创建一个合并的文件（但结构更清晰）
    # 使用外连接合并，确保理论和仿真数据分别保存
    combined_df = pd.concat([theory_pivot, sim_pivot], axis=1, sort=True)
    combined_df.index.name = x_param_name
    
    wide_output_filename = f'combined_results_by_{x_param_name}.csv'
    combined_df.to_csv(wide_output_filename)
    print(f"合并数据已保存到文件：{wide_output_filename}")
    print("合并数据前几行预览：")
    print(combined_df.head())

    # --- Print detailed comparison table for the first discrete point ---
    if len(discrete_sim_x_values) > 0:
        example_x_val = discrete_sim_x_values[0]
        print(f"\n--- 详细对比表格 (针对 {x_param_name} = {example_x_val}) ---")
        try:
            lambda_for_table = example_x_val if x_param_name == 'lambda' else DISCRETE_SIM_LAMBDA_VALUES
            m_for_table = example_x_val if x_param_name == 'M' else DISCRETE_SIM_M_VALUES
            epsilon_for_table = example_x_val if x_param_name == 'epsilon' else DISCRETE_SIM_EPSILON_VALUES
            p_for_table = example_x_val if x_param_name == 'p' else 0.1  # 默认p值

            dpki_upper_for_table = theoretical_values_dpki_upper_bound(lambda_for_table, p_for_table,
                                                                       Q_MANAGE_SINGLE, MU_BASE_SINGLE, m_for_table,
                                                                       GAMMA_HIGH_SECURITY_SINGLE,
                                                                       LAMBDA_P_BLOCK_RATE_SINGLE, epsilon_for_table)
            dpki_lower_for_table = theoretical_values_dpki_lower_bound(lambda_for_table, p_for_table,
                                                                       Q_MANAGE_SINGLE, MU_BASE_SINGLE, m_for_table,
                                                                       GAMMA_HIGH_SECURITY_SINGLE,
                                                                       LAMBDA_P_BLOCK_RATE_SINGLE, epsilon_for_table)
            dpki_sim_for_table = run_simulation_dpki_model(lambda_for_table, p_for_table, Q_MANAGE_SINGLE,
                                                           MU_BASE_SINGLE, m_for_table, GAMMA_HIGH_SECURITY_SINGLE,
                                                           LAMBDA_P_BLOCK_RATE_SINGLE, SIM_TIME, WARMUP_TIME,
                                                           epsilon_for_table)
            pki_theory_w_total_for_table, _ = theory_fcfs_values(m_for_table, lambda_for_table, p_for_table,
                                                                 MU_BASE_SINGLE, Q_MANAGE_SINGLE, epsilon_for_table)

            print(f"--- 实际仿真流量比例 (针对 {x_param_name} = {example_x_val}) ---")
            print(f"实际链上请求比例 (仿真): {dpki_sim_for_table['actual_P_on_chain_sim']:.4f}")
            print(f"实际链下请求比例 (仿真): {dpki_sim_for_table['actual_P_off_chain_sim']:.4f}")
            print("-" * 40)
            print("\n" + "=" * 100)
            print(f"--- DPKI 模型理论值 vs. 仿真值对比 (针对 {x_param_name}={example_x_val:.3f}) ---")
            print("--------------------------------------------------")
            print("{:<30} {:<15} {:<15} {:<15} {:<15}".format("指标", "DPKI上界(理论)", "DPKI下界(理论)",
                                                              "DPKI实际(仿真)", "PKI(理论)"))
            print("-" * 100)
            print("{:<30} {:<15.5f} {:<15.5f} {:<15.5f} {:<15.5f}".format(
                "总平均时延 (E_total)",
                dpki_upper_for_table['E_T_total'],
                dpki_lower_for_table['E_T_total'],
                dpki_sim_for_table['E_T_total'],
                pki_theory_w_total_for_table
            ))
            print("-" * 100)
            print("{:<30} {:<15.5f} {:<15.5f} {:<15.5f} {:<15}".format(
                "低安全认证时延 (Stage 1)",
                dpki_upper_for_table['E_T_stage1_upper'],
                dpki_lower_for_table['E_T_stage1_lower'],
                dpki_sim_for_table['E_T_stage1_sim'],
                "不适用"
            ))
            print("{:<30} {:<15.5f} {:<15.5f} {:<15.5f} {:<15}".format(
                "交易池/打包时延 (Stage 2)",
                dpki_upper_for_table['E_T_stage2_upper'],
                dpki_lower_for_table['E_T_stage2_lower'],
                dpki_sim_for_table['E_T_stage2_sim'],
                "不适用"
            ))
            print("{:<30} {:<15.5f} {:<15.5f} {:<15.5f} {:<15}".format(
                "On-chain确认时延 (Stage 3)",
                dpki_upper_for_table['E_T_stage3_upper'],
                dpki_lower_for_table['E_T_stage3_lower'],
                dpki_sim_for_table['E_T_stage3_sim'],
                "不适用"
            ))
            print("=" * 100)

        except Exception as e:
            print(f"生成详细对比表格失败: {e}")
    else:
        print(f"\n没有离散 {x_param_name} 值用于生成详细对比表格。")

    # --- Plotting (unchanged aesthetics) ---
    plt.figure(figsize=(12, 7))

    pki_fcfs_theory_df = final_df[(final_df['source'] == 'Theory') & (final_df['model'] == 'PKI FCFS')]
    pki_fcfs_sim_df = final_df[(final_df['source'] == 'Simulation') & (final_df['model'] == 'PKI FCFS')]
    dpki_upper_theory_df = final_df[(final_df['source'] == 'Theory') & (final_df['model'] == 'DPKI Upper')]
    dpki_lower_theory_df = final_df[(final_df['source'] == 'Theory') & (final_df['model'] == 'DPKI Lower')]
    dpki_real_situation_sim_df = final_df[(final_df['source'] == 'Simulation') & (final_df['model'] == 'DPKI Real')]

    plt.plot(dpki_upper_theory_df[x_param_name], dpki_upper_theory_df['E_T_total'], label='DPKI upper', linestyle='--',
             linewidth=2)
    plt.plot(dpki_lower_theory_df[x_param_name], dpki_lower_theory_df['E_T_total'], label='DPKI lower', linestyle=':',
             linewidth=2)
    plt.plot(dpki_real_situation_sim_df[x_param_name], dpki_real_situation_sim_df['E_T_total'], label='DPKI simu',
             marker='x', markersize=8, linestyle='-', linewidth=1.5)

    plt.plot(pki_fcfs_theory_df[x_param_name], pki_fcfs_theory_df['E_T_total'], label='PKI theory', linestyle='-',
             linewidth=2)
    plt.plot(pki_fcfs_sim_df[x_param_name], pki_fcfs_sim_df['E_T_total'], label='PKI comparison', marker='o',
             markersize=6, linestyle='None')

    plt.xlabel(x_param_label, fontsize=12)
    plt.ylabel('$E_{total}$ (total latency)', fontsize=12)
    plt.title(f'Comparison ($E_{{total}}$) vs. {x_param_label}', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()