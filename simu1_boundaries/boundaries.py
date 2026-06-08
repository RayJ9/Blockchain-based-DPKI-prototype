import numpy as np
import pandas as pd
import math
import heapq
from collections import deque
import matplotlib.pyplot as plt
import random

# ------------------ Core queueing utilities (unchanged) ------------------

def erlang_c_probability(m, rho_low):
    if rho_low >= 1:
        return 1.0
    numerator = ((m * rho_low)**m / math.factorial(m)) * (1 / (1 - rho_low))
    sum_part_denominator = sum((m * rho_low)**i / math.factorial(i) for i in range(m))
    denominator = sum_part_denominator + numerator
    if denominator == 0:
        return 0.0
    return numerator / denominator

def theoretical_values_dpki_upper_bound(lambd, p, q, mu, m, gamma, lambd_p, epsilon):
    rho_low = ((1 - p)*(1 - gamma)*(1 - epsilon) * lambd) / (m * mu)
    if rho_low >= 1:
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
    E_Wq_low = (C_m_rho_low) / (mu * m -(1 - p)*(1 - gamma)*(1 - epsilon) * lambd)
    E_S_low = 1 / mu
    E_T_low = E_Wq_low + E_S_low

    lambd_n = (gamma * (1 - p)  + p + (1 - p) * (1 - gamma) * epsilon) * lambd
    E_T_stage2_mempool = 1 / lambd_p

    if lambd_n == 0:
        E_S_tx_weighted_theory = 0.0
        E_W_tx_weighted_theory = 0.0
        rho = 0.0
    else:
        p_n = (p * lambd) / lambd_n
        E_B = lambd_n / lambd_p
        Var_B = E_B + E_B**2
        E_B2 = Var_B + E_B**2
        E_Si_avg = (p_n / (q * mu) + (1 - p_n) / mu)
        E_S_batch = E_B * E_Si_avg
        E_Si2_mgmt = 2 / (q * mu)**2
        E_Si2_auth = 2 / mu**2
        E_Si_sq_avg = p_n * E_Si2_mgmt + (1 - p_n) * E_Si2_auth
        Var_Si = E_Si_sq_avg - E_Si_avg**2
        E_S_batch2 = E_B * Var_Si + E_B2 * (E_Si_avg)**2

        rho = lambd_p * E_S_batch
        if rho >= 1:
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
        E_W_tx_weighted_theory = E_W_batch

    E_T_stage3_upper = E_W_tx_weighted_theory + E_S_tx_weighted_theory
    E_T_total = ((1 - p)*gamma + p + (1 - p)*(1 - gamma)*epsilon) * (E_T_stage2_mempool + E_T_stage3_upper) + \
                ((1 - p)*(1 - gamma)*(1 - epsilon) * E_T_low)

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
    stability_check = q * mu - p_n * lambd_n - (1 - p_n) * q * lambd_n
    if stability_check <= 0:
        return float('inf')
    numerator = (lambd_n / (q * mu)) * (p_n + (1 - p_n) * q**2)
    denominator = stability_check
    if denominator == 0:
        return float('inf')
    return numerator / denominator

def theoretical_values_dpki_lower_bound(lambd, p, q, mu, m, gamma, lambd_p, epsilon):
    rho_low = ((1 - p)*(1 - gamma)*(1 - epsilon) * lambd) / (m * mu)
    if rho_low >= 1:
        return {
            'model': 'DPKI Lower Bound',
            'E_T_total': float('inf'),
            'E_T_stage1_lower': float('inf'),
            'E_T_stage2_lower': float('inf'),
            'E_T_stage3_lower': float('inf')
        }
    C_m_rho_low = erlang_c_probability(m, rho_low)
    E_Wq_low = (C_m_rho_low) / (mu * m * (1 - rho_low))
    E_S_low = 1 / mu
    E_T_low = E_Wq_low + E_S_low

    lambd_n = (gamma * (1 - p)  + p + (1 - p) * (1 - gamma) * epsilon) * lambd
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
    E_T_total_lower = ((1 - p)*gamma + p + (1 - p)*(1 - gamma)*epsilon) * (E_T_stage2_mempool_lower + E_T_stage3_lower) + \
                      ((1 - p)*(1 - gamma)*(1 - epsilon) * E_T_low)
    return {
        'model': 'DPKI Lower Bound',
        'E_T_total': E_T_total_lower,
        'E_T_stage1_lower': E_T_low,
        'E_T_stage2_lower': E_T_stage2_mempool_lower,
        'E_T_stage3_lower': E_T_stage3_lower
    }

def run_simulation_dpki_model(lambd, p_mgmt, q, mu, m, gamma_from_low_sec, lambd_p,
                              T_end, T_warmup=0.0, epsilon=0.0):
    """
    轻量版：只用累计量，不存每个请求。
    保持与原函数相同的返回字段。
    """
    # ---- 参数/速率 ----
    p = float(p_mgmt)
    q = float(q)
    mu = float(mu)
    m = int(m)
    gamma = float(gamma_from_low_sec)
    eps = float(epsilon)

    # 上链/链下到达率（与原逻辑一致）
    lambda_on = (gamma * (1 - p) + p + (1 - p) * (1 - gamma) * eps) * lambd
    lambda_off = (1 - p) * (1 - gamma) * (1 - eps) * lambd

    # ---- 事件队列： (time, type, payload...) ----
    # 事件类型用小整数减少对象体积
    EVT_ARR_ON  = 0
    EVT_ARR_OFF = 1
    EVT_LOW_END = 2
    EVT_BLOCK   = 3
    EVT_MG1_END = 4

    import heapq, random
    from collections import deque

    now = 0.0
    evq = []

    # 预排第一批到达&出块
    if lambda_on  > 0: heapq.heappush(evq, (now + random.expovariate(lambda_on),  EVT_ARR_ON))
    if lambda_off > 0: heapq.heappush(evq, (now + random.expovariate(lambda_off), EVT_ARR_OFF))
    if lambd_p    > 0: heapq.heappush(evq, (now + random.expovariate(lambd_p),    EVT_BLOCK))

    # ---- 队列状态（只存必要的标量）----
    # 低安全：到达时间队列（只放 float）；分配服务时把必要信息带入完成事件
    low_q = deque()
    # m 个并行低安全服务器：空闲数+正在服务的个体通过事件传回
    low_busy = 0

    # mempool：只存 (arrival_time, is_warm)；不存 ID
    mempool = deque()

    # 区块在 M/G/1 的队列：只存聚合信息
    # 每个元素是 dict: { 'arrival': block_gen_time,
    #                    'service': block_service_time,
    #                    'Bwarm': 进入该块且暖机后到达的交易个数,
    #                    'sum_arr_warm': 上述暖机后到达交易的到达时间之和 }
    mg1_q = deque()
    mg1_server_free_time = 0.0

    # ---- 统计量（仅对“暖机后到达”的请求计入）----
    warm = False
    # 统计总完成请求数（暖机后到达）
    n_done_total = 0
    # 阶段延时与总延时的累计和
    sum_total_latency = 0.0
    sum_stage1 = 0.0
    sum_stage2 = 0.0
    sum_stage3 = 0.0

    # 路径占比（暖机后到达的完成数）
    n_onchain_done = 0
    n_offchain_done = 0

    # MG1 忙碌时间精确累计（与暖机区间的交叠）
    mg1_busy_after_warm = 0.0

    # ---- 工具：采样指数分布 ----
    exp = random.expovariate

    # ---- 主循环 ----
    while evq and now < T_end:
        now, etype, *edata = heapq.heappop(evq)

        # 切换到 warmup 后：从这一刻开始，只统计“此后到达”的请求
        if (not warm) and now >= T_warmup:
            warm = True
            # 注意：队列里已在 warmup 前到达的请求仍会完成；它们不应计入统计。
            # 我们靠“是否暖机后到达”的标记在下方区分。

        if etype == EVT_ARR_ON:
            # 上链到达：系统初始到达时间 = mempool 到达时间
            is_warm = warm  # 这个请求是否在暖机之后到达
            mempool.append((now, is_warm))
            if lambda_on > 0 and now < T_end:
                heapq.heappush(evq, (now + exp(lambda_on), EVT_ARR_ON))

        elif etype == EVT_ARR_OFF:
            # 链下到达：排入低安全队列
            low_q.append((now, warm))  # (arrival_time, is_warm)
            if lambda_off > 0 and now < T_end:
                heapq.heappush(evq, (now + exp(lambda_off), EVT_ARR_OFF))

            # 若有空闲低安全服务器，立即派工
            while low_busy < m and low_q:
                arr_t, is_warm_arr = low_q.popleft()
                low_busy += 1
                svc_time = exp(mu)  # 低安全服务~Exp(mu)
                # 完成事件携带到达时间和是否暖机
                heapq.heappush(evq, (now + svc_time, EVT_LOW_END, arr_t, is_warm_arr))

        elif etype == EVT_LOW_END:
            # 低安全完成
            arr_t, is_warm_arr = edata  # 来自派工时传入
            low_busy -= 1
            if is_warm_arr:
                # 总延时 = 完成时刻 - 到达时刻
                delay = now - arr_t
                n_done_total += 1
                n_offchain_done += 1
                sum_total_latency += delay
                sum_stage1 += delay  # Stage2/3 为 0

            # 看看是否还能继续派工
            while low_busy < m and low_q:
                arr_t2, is_warm2 = low_q.popleft()
                low_busy += 1
                svc_time2 = exp(mu)
                heapq.heappush(evq, (now + svc_time2, EVT_LOW_END, arr_t2, is_warm2))

        elif etype == EVT_BLOCK:
            # 区块生成：把 mempool 里的交易全部打包，做“聚合统计”
            B = len(mempool)
            if B > 0:
                # 分离“暖机后到达”的子集：我们只需要 (计数, 到达时间和)，无需逐个存档
                Bwarm = 0
                sum_arr_warm = 0.0
                # 计算区块服务时间（逐笔累加的总和），同时清空 mempool
                total_service_time = 0.0

                # 预先计算：上链交易中“管理类”的概率（与你原逻辑一致）
                prob_mgmt_on_chain = 0.0
                if lambda_on > 0:
                    prob_mgmt_on_chain = (p * lambd) / lambda_on

                while mempool:
                    arr_t, is_warm_arr = mempool.popleft()
                    if is_warm_arr:
                        Bwarm += 1
                        sum_arr_warm += arr_t
                    # 服务时间抽样
                    if random.random() < prob_mgmt_on_chain:
                        total_service_time += exp(q * mu)
                    else:
                        total_service_time += exp(mu)

                # 该区块进入 MG1
                mg1_q.append({
                    'arrival': now,                # 区块生成时刻
                    'service': total_service_time, # 整块服务时间之和
                    'Bwarm': Bwarm,                # 暖机后到达的交易个数
                    'sum_arr_warm': sum_arr_warm   # 对应到达时间之和
                })

                # 若 MG1 空闲，立即开工
                if mg1_server_free_time <= now:
                    blk = mg1_q.popleft()
                    start = max(blk['arrival'], now, mg1_server_free_time)
                    finish = start + blk['service']
                    # 累加忙时（与暖机区间的交集长度）
                    if finish > T_warmup:
                        s = max(start, T_warmup)
                        f = finish
                        if f > s:
                            mg1_busy_after_warm += (f - s)
                    mg1_server_free_time = finish
                    heapq.heappush(evq, (finish, EVT_MG1_END, blk, start, finish))

            # 下一次出块
            if lambd_p > 0 and now < T_end:
                heapq.heappush(evq, (now + exp(lambd_p), EVT_BLOCK))

        elif etype == EVT_MG1_END:
            # 区块完成：一次性把该块中“暖机后到达”的交易的延时统统累到累加器
            blk, start, finish = edata
            Bwarm = blk['Bwarm']
            if Bwarm > 0:
                # Stage2（mempool等待）总和 = sum_{warm}( block_time - arrival_time )
                sum_stage2 += Bwarm * blk['arrival'] - blk['sum_arr_warm']
                # Stage3（区块服务+前序等待）总和 = sum_{warm}( finish - block_time )
                sum_stage3 += Bwarm * (finish - blk['arrival'])
                # 总延时 = sum_{warm}( finish - arrival_time )
                sum_total_latency += Bwarm * finish - blk['sum_arr_warm']
                n_done_total += Bwarm
                n_onchain_done += Bwarm

            # MG1 若还有块，继续
            if mg1_q:
                blk2 = mg1_q.popleft()
                start2 = max(blk2['arrival'], now, mg1_server_free_time)
                finish2 = start2 + blk2['service']
                if finish2 > T_warmup:
                    s2 = max(start2, T_warmup)
                    f2 = finish2
                    if f2 > s2:
                        mg1_busy_after_warm += (f2 - s2)
                mg1_server_free_time = finish2
                heapq.heappush(evq, (finish2, EVT_MG1_END, blk2, start2, finish2))

    # ---- 汇总 ----
    if n_done_total == 0:
        return {
            'model': 'DPKI Full Sim',
            'E_T_total': np.nan,
            'E_T_stage1_sim': np.nan,
            'E_T_stage2_sim': np.nan,
            'E_T_stage3_sim': np.nan,
            'rho_sim': np.nan,
            'actual_P_on_chain_sim': np.nan,
            'actual_P_off_chain_sim': np.nan
        }

    E_T_total = sum_total_latency / n_done_total
    E_T_stage1 = (sum_stage1 / n_done_total) if n_done_total else np.nan
    E_T_stage2 = (sum_stage2 / n_done_total) if n_done_total else np.nan
    E_T_stage3 = (sum_stage3 / n_done_total) if n_done_total else np.nan

    dur = max(T_end - max(T_warmup, 0.0), 1e-9)
    rho_sim = mg1_busy_after_warm / dur

    P_on = n_onchain_done / n_done_total
    P_off = n_offchain_done / n_done_total

    return {
        'model': 'DPKI Full Sim',
        'E_T_total': E_T_total,
        'E_T_stage1_sim': E_T_stage1,
        'E_T_stage2_sim': E_T_stage2,
        'E_T_stage3_sim': E_T_stage3,
        'rho_sim': min(1.0, max(0.0, rho_sim)),
        'actual_P_on_chain_sim': P_on,
        'actual_P_off_chain_sim': P_off
    }


# ------------------ Main: plot E(T) vs lambda for 3 lambda_p ------------------

if __name__ == '__main__':
    # Fixed system parameters (your defaults)
    P_MANAGE_SINGLE = 0.1
    Q_MANAGE_SINGLE = 0.1
    MU_BASE_SINGLE = 10
    GAMMA_HIGH_SECURITY_SINGLE = 0.1
    DISCRETE_SIM_M_VALUES = 4
    DISCRETE_SIM_EPSILON_VALUES = 0.1

    # New: three λ_p values with reasonably tight bounds
    LAMBDA_P_LIST = [2,4,6]

    # X-axis: lambda sweep (theory) and discrete points (simulation)
    LAMBDA_MIN, LAMBDA_MAX, NUM_THEORY_POINTS = 1, 6, 100
    THEORY_LAMBDA_VALUES = np.linspace(LAMBDA_MIN, LAMBDA_MAX, NUM_THEORY_POINTS)
    DISCRETE_SIM_LAMBDA_VALUES = np.array([1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8])

    # Simulation horizon
    SIM_TIME = 1_000_000
    WARMUP_TIME = 10_000

    print("--- Configuration ---")
    print(f"λ range for theory: [{LAMBDA_MIN}, {LAMBDA_MAX}] with {NUM_THEORY_POINTS} points")
    print(f"Discrete λ for simulation: {DISCRETE_SIM_LAMBDA_VALUES}")
    print(f"λ_p values: {LAMBDA_P_LIST}")
    print(f"m (low-security servers): {DISCRETE_SIM_M_VALUES}")
    print(f"ε (retry prob.): {DISCRETE_SIM_EPSILON_VALUES}")
    print(f"p (mgmt. fraction): {P_MANAGE_SINGLE}, q (mgmt. speed factor): {Q_MANAGE_SINGLE}, μ: {MU_BASE_SINGLE}, γ: {GAMMA_HIGH_SECURITY_SINGLE}")
    print(f"SIM_TIME: {SIM_TIME}, WARMUP_TIME: {WARMUP_TIME}")
    print("-"*40)

    # Containers for CSV
    all_rows = []

    # Plot
    plt.figure(figsize=(11, 7))

    for lambda_p in LAMBDA_P_LIST:
        # --- Theory curves across dense λ grid ---
        upper_points = []
        lower_points = []
        for lam in THEORY_LAMBDA_VALUES:
            up = theoretical_values_dpki_upper_bound(
                lam, P_MANAGE_SINGLE, Q_MANAGE_SINGLE, MU_BASE_SINGLE,
                DISCRETE_SIM_M_VALUES, GAMMA_HIGH_SECURITY_SINGLE, lambda_p, DISCRETE_SIM_EPSILON_VALUES
            )
            lo = theoretical_values_dpki_lower_bound(
                lam, P_MANAGE_SINGLE, Q_MANAGE_SINGLE, MU_BASE_SINGLE,
                DISCRETE_SIM_M_VALUES, GAMMA_HIGH_SECURITY_SINGLE, lambda_p, DISCRETE_SIM_EPSILON_VALUES
            )
            upper_points.append((lam, up['E_T_total']))
            lower_points.append((lam, lo['E_T_total']))
            all_rows.append({'lambda': lam, 'lambda_p': lambda_p, 'curve': 'dpki_upper_theory', 'E_total': up['E_T_total']})
            all_rows.append({'lambda': lam, 'lambda_p': lambda_p, 'curve': 'dpki_lower_theory', 'E_total': lo['E_T_total']})

        # Plot theory (no explicit colors to keep plotting generic)
        plt.plot([x for x, y in upper_points], [y for x, y in upper_points],
                 linestyle='--', linewidth=2, label=f'Upper (λp={lambda_p})')
        plt.plot([x for x, y in lower_points], [y for x, y in lower_points],
                 linestyle=':', linewidth=2, label=f'Lower (λp={lambda_p})')

        # --- Simulation points on discrete λ values ---
        sim_points = []
        for lam in DISCRETE_SIM_LAMBDA_VALUES:
            sim_res = run_simulation_dpki_model(
                lam, P_MANAGE_SINGLE, Q_MANAGE_SINGLE, MU_BASE_SINGLE,
                DISCRETE_SIM_M_VALUES, GAMMA_HIGH_SECURITY_SINGLE, lambda_p,
                SIM_TIME, WARMUP_TIME, DISCRETE_SIM_EPSILON_VALUES
            )
            sim_points.append((lam, sim_res['E_T_total']))
            all_rows.append({'lambda': lam, 'lambda_p': lambda_p, 'curve': 'dpki_sim', 'E_total': sim_res['E_T_total']})
            print(f"λp={lambda_p:.2f}, λ={lam:.2f}: DPKI sim E_total={sim_res['E_T_total']:.5f}, ρ_stage3≈{sim_res['rho_sim']:.4f}")

        plt.plot([x for x, y in sim_points], [y for x, y in sim_points],
                 marker='o', linestyle='-', linewidth=1.5, label=f'Sim (λp={lambda_p})')

    # Cosmetics
    plt.xlabel(r'$\lambda$ (total arrival)')
    plt.ylabel(r'$E(T)$')
    plt.title(r'$\;E(T)$ vs. $\lambda$ for three $\lambda_p$ values (upper/lower bounds and simulation)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(ncol=3, fontsize=9)
    plt.tight_layout()

    # Save CSV (wide format helps downstream analysis)
    df_long = pd.DataFrame(all_rows)
    df_wide = df_long.pivot_table(index='lambda', columns=['lambda_p', 'curve'], values='E_total', aggfunc='first')
    df_wide = df_wide.sort_index(axis=0).sort_index(axis=1)
    df_wide.to_csv('etotal_vs_lambda_by_lambdap.csv', float_format='%.6f')
    print("\nSaved: etotal_vs_lambda_by_lambdap.csv")

    plt.show()
