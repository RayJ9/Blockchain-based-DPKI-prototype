import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import brentq


# ==============================================================================
# SECTION 1: LATENCY & QUEUEING HELPER FUNCTIONS (保持不变)
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


def get_tail_prob_on_chain(ts, model_type, params):
    mean_latency_func = \
    {'pki': get_mean_latency_pki, 'dpki_lower': get_mean_latency_dpki_lower, 'dpki_upper': get_mean_latency_dpki_upper}[
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
# SECTION 2: AVAILABILITY CALCULATION FUNCTIONS (保持不变)
# ==============================================================================
def binomial_prob(n, k, p):
    if k < 0 or k > n: return 0
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def calculate_availability_pki(pf, ts, params):
    Fi = min(pf + pf * (1 - pf) * (1 - params['p']) * params['epsilon'], 1.0)
    Ft = get_tail_prob_on_chain(ts, 'pki', params)
    return (1 - Fi) * (1 - Ft)


def calculate_availability_dpki_malicious(pf, ts, p_th, params):
    """
    Calculates DPKI Availability for "Malicious" scenario using binomial distribution.
    This provides a weighted average over all possible numbers of malicious nodes.
    """
    bounds = {'lower': 0.0, 'upper': 0.0}
    total_m = params['m']
    k_threshold = math.ceil(total_m * p_th)  # Number of nodes to break consensus

    # Pre-calculate components that don't depend on k
    lambda_a = params['lambd'] * (1 - params['p']) * (1 - params['gamma']) * (1 - params['epsilon'])
    lambda_b = params['lambd'] - lambda_a

    # Sum the weighted availabilities over k=0 to m malicious nodes
    for k in range(total_m + 1):
        # Probability of having exactly k malicious nodes
        prob_k_malicious = binomial_prob(total_m, k, pf)

        # Availability given k malicious nodes (A_k)
        # Per Eq. (39), if k reaches threshold, availability for this state is 0
        if k >= k_threshold:
            avail_k_lower = 0.0
            avail_k_upper = 0.0
        else:
            # Per Eq. (40) logic, calculate the new effective load for this state
            # Extra load is proportional to the FRACTION of malicious nodes (k/m)
            extra_load = (k / total_m) * lambda_a if total_m > 0 else 0

            lambda_b_prime = lambda_b + extra_load
            scaling_factor = lambda_b_prime / lambda_b if lambda_b > 0 else 1.0

            mod_params = params.copy()
            mod_params['lambd'] = params['lambd'] * scaling_factor

            # Calculate Ft for this specific state k
            Ft_lower = get_tail_prob_on_chain(ts, 'dpki_lower', mod_params)
            Ft_upper = get_tail_prob_on_chain(ts, 'dpki_upper', mod_params)

            avail_k_lower = 1 - Ft_lower
            avail_k_upper = 1 - Ft_upper

        # Add to the total expected availability
        bounds['lower'] += prob_k_malicious * avail_k_lower
        bounds['upper'] += prob_k_malicious * avail_k_upper

    return bounds['lower'], bounds['upper']


# ==============================================================================
# SECTION 3: 新的主函数 - 可视化A同时受λ和M影响
# ==============================================================================
if __name__ == '__main__':
    # --- 1. 设置参数范围 ---
    # pf (恶意节点概率) 的范围
    PF_VALUES = np.linspace(1.0, 0.0, 30)  # 从1.0到0.0，大值在前
    # M (服务CA数量) 的范围  
    M_VALUES = np.array([4, 5, 6, 7, 8, 9, 10, 11, 12])  # 9个M值
    
    # 固定其他参数
    BASE_PARAMS = {
        'p': 0.1, 'q': 0.3, 'mu': 7.5,
        'gamma': 0.1, 'epsilon': 0.1, 'lambda_p': 10
    }
    
    # 固定λ和其他参数
    FIXED_LAMBDA = 2.0  # 固定总到达率为2.0
    TIMEOUT_THRESHOLD_TS = 0.6
    CONSENSUS_THRESHOLD_P_TH = 0.5
    
    print("--- 开始计算系统可用性A受pf和M同时影响的分析 ---")
    print(f"pf范围: {PF_VALUES.min():.1f} - {PF_VALUES.max():.1f}")
    print(f"M范围: {M_VALUES.min()} - {M_VALUES.max()}")
    print(f"固定参数: λ={FIXED_LAMBDA}, ts={TIMEOUT_THRESHOLD_TS}, p_th={CONSENSUS_THRESHOLD_P_TH}")
    
    # --- 2. 计算可用性数据 ---
    results = []
    total_combinations = len(PF_VALUES) * len(M_VALUES)
    current_count = 0
    
    for pf in PF_VALUES:
        for m in M_VALUES:
            current_count += 1
            if current_count % 50 == 0:
                print(f"进度: {current_count}/{total_combinations} ({100*current_count/total_combinations:.1f}%)")
            
            # 设置当前参数
            current_params = BASE_PARAMS.copy()
            current_params['lambd'] = FIXED_LAMBDA
            current_params['m'] = m
            
            # 计算PKI可用性
            try:
                avail_pki = calculate_availability_pki(pf, TIMEOUT_THRESHOLD_TS, current_params)
            except:
                avail_pki = 0.0
            
            # 计算DPKI可用性
            try:
                dpki_lower, dpki_upper = calculate_availability_dpki_malicious(
                    pf, TIMEOUT_THRESHOLD_TS, CONSENSUS_THRESHOLD_P_TH, current_params)
            except:
                dpki_lower, dpki_upper = 0.0, 0.0
            
            results.append({
                'pf': pf,
                'm': m,
                'PKI': avail_pki,
                'DPKI_Lower': dpki_lower,
                'DPKI_Upper': dpki_upper,
                'DPKI_Mean': (dpki_lower + dpki_upper) / 2
            })
    
    # 转换为DataFrame
    df = pd.DataFrame(results)
    print("计算完成！")
    
    # --- 3. 创建3D切面可视化 ---
    # 创建单个3D图形
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # 移除背景和网格
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('none')
    ax.yaxis.pane.set_edgecolor('none')
    ax.zaxis.pane.set_edgecolor('none')
    ax.grid(False)
    
    # 为每个M值创建切面
    colors_pki = plt.cm.Reds(np.linspace(0.4, 0.9, len(M_VALUES)))
    colors_dpki = plt.cm.Blues(np.linspace(0.4, 0.9, len(M_VALUES)))
    
    for i, m in enumerate(M_VALUES):
        # 获取当前M值对应的数据
        m_data = df[df['m'] == m].sort_values('pf')
        pf_vals = m_data['pf'].values
        pki_vals = m_data['PKI'].values
        dpki_vals = m_data['DPKI_Mean'].values
        
        # 首先绘制白色底色平面
        pf_mesh = np.tile(pf_vals, (2, 1))  # 2行，每行都是pf_vals
        m_mesh = np.full_like(pf_mesh, m)   # 所有点的M坐标都是当前m值
        
        # 创建淡灰色底色平面 - 放在最底部
        white_mesh = np.zeros_like(pf_mesh)  # Z坐标为0的平面
        ax.plot_surface(pf_mesh, m_mesh, white_mesh, 
                       color='lightgray', alpha=0.3, 
                       linewidth=0, antialiased=True)
        
        # PKI切面平面 - 放在白色底色之上
        pki_mesh = np.array([pki_vals, pki_vals])  # 2行相同的PKI值
        ax.plot_surface(pf_mesh, m_mesh, pki_mesh, 
                       color=colors_pki[i], alpha=0.7, 
                       linewidth=0, antialiased=True,
                       label=f'PKI M={m}')
        
        # DPKI切面平面 - 稍微偏移一点避免重叠
        dpki_mesh = np.array([dpki_vals, dpki_vals])
        m_mesh_dpki = m_mesh + 0.05  # 轻微偏移
        ax.plot_surface(pf_mesh, m_mesh_dpki, dpki_mesh, 
                       color=colors_dpki[i], alpha=0.7, 
                       linewidth=0, antialiased=True,
                       label=f'DPKI M={m}')
        
        # 添加边界线条以突出切面轮廓
        ax.plot(pf_vals, np.full_like(pf_vals, m), pki_vals, 
                color=colors_pki[i], linewidth=2.5, alpha=0.9)
        ax.plot(pf_vals, np.full_like(pf_vals, m+0.05), dpki_vals, 
                color=colors_dpki[i], linewidth=2.5, alpha=0.9, linestyle='--')
    
    # 设置坐标轴标签和标题
    ax.set_xlabel('恶意节点概率 pf', fontsize=14, labelpad=10)
    ax.set_ylabel('服务CA数量 M', fontsize=14, labelpad=10)
    ax.set_zlabel('系统可用性 A', fontsize=14, labelpad=10)
    ax.set_title(f'PKI vs DPKI 系统可用性 3D 切面图\n(λ={FIXED_LAMBDA})', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # 设置坐标轴范围
    ax.set_xlim(PF_VALUES.min(), PF_VALUES.max())
    ax.set_ylim(M_VALUES.min()-0.5, M_VALUES.max()+0.5)
    ax.set_zlim(0, 1)
    
    # 创建自定义图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.6, label='PKI'),
        Patch(facecolor='blue', alpha=0.6, label='DPKI')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=12)
    
    # 调整视角
    ax.view_init(elev=25, azim=45)
    
    plt.tight_layout()
    
    # 保存图像
    plt.savefig('availability_pf_m_slices_3d.png', dpi=300, bbox_inches='tight')
    print("3D切面图已保存为: availability_pf_m_slices_3d.png")
    
    # 保存数据
    df.to_csv('availability_pf_m_slices_3d_data.csv', index=False)
    print("数据已保存为: availability_pf_m_slices_3d_data.csv")
    
    plt.show()
    
    # --- 4. 输出关键统计信息 ---
    print("\n=== 关键统计信息 ===")
    print(f"PKI最大可用性: {df['PKI'].max():.4f}")
    print(f"PKI最小可用性: {df['PKI'].min():.4f}")
    print(f"DPKI最大可用性: {df['DPKI_Mean'].max():.4f}")
    print(f"DPKI最小可用性: {df['DPKI_Mean'].min():.4f}")
    
    # 找到最优配置
    best_pki_idx = df['PKI'].idxmax()
    best_dpki_idx = df['DPKI_Mean'].idxmax()
    
    print(f"\nPKI最优配置: pf={df.loc[best_pki_idx, 'pf']:.2f}, M={df.loc[best_pki_idx, 'm']}, A={df.loc[best_pki_idx, 'PKI']:.4f}")
    print(f"DPKI最优配置: pf={df.loc[best_dpki_idx, 'pf']:.2f}, M={df.loc[best_dpki_idx, 'm']}, A={df.loc[best_dpki_idx, 'DPKI_Mean']:.4f}")