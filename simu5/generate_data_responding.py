import numpy as np
import pandas as pd
import math
from scipy.optimize import brentq

# 直接从simu5_ava_p导入所有计算函数
from simu5_ava_p import (
    erlang_c_probability,
    get_mean_latency_pki,
    get_mean_latency_dpki_lower,
    get_mean_latency_dpki_upper,
    get_tail_prob_M_M_m,
    get_tail_prob_on_chain,
    binomial_prob,
    calculate_availability_pki,
    calculate_availability_dpki_responding
)

# 快速生成数据 - 基于"Nodes Not Responding"场景
def generate_responding_data():
    # 使用与simu5_ava_p相同的基础参数
    BASE_PARAMS = {
        'lambd': 3.0, 'p': 0.1, 'q': 0.3, 'mu': 7.5,
        'gamma': 0.3, 'epsilon': 0.1, 'lambda_p': 10, 'm': 24
    }
    
    # 使用与当前场景相同的网格设置以保持一致性
    pf_values = np.linspace(0, 1.0, 50)  # 50x50网格
    ts_values = np.linspace(0.5, 1.5, 50)    # 0.5-1.5范围
    
    PF, TS = np.meshgrid(pf_values, ts_values)
    PKI_AVAIL = np.zeros_like(PF)
    DPKI_LOWER = np.zeros_like(PF)
    DPKI_UPPER = np.zeros_like(PF)
    
    print("正在生成'Nodes Not Responding'场景的3D数据...")
    print(f"基础参数: {BASE_PARAMS}")
    print(f"网格大小: {PF.shape[0]} x {PF.shape[1]}")
    
    total_points = PF.shape[0] * PF.shape[1]
    
    for i in range(PF.shape[0]):
        for j in range(PF.shape[1]):
            pf = PF[i, j]
            ts = TS[i, j]
            
            # 计算PKI可用性
            pki_avail = calculate_availability_pki(pf, ts, BASE_PARAMS)
            
            # 计算DPKI可用性 - 使用responding场景的计算函数
            dpki_lower, dpki_upper = calculate_availability_dpki_responding(pf, ts, BASE_PARAMS)
            
            PKI_AVAIL[i, j] = pki_avail
            DPKI_LOWER[i, j] = dpki_lower
            DPKI_UPPER[i, j] = dpki_upper
        
        progress = ((i + 1) * PF.shape[1]) / total_points * 100
        if i % 5 == 0:
            print(f"进度: {progress:.1f}%")
    
    # 保存数据 - 与当前场景相同的格式
    data_dict = {
        'pf': PF.flatten(),
        'ts': TS.flatten(),
        'pki_availability': PKI_AVAIL.flatten(),
        'dpki_lower': DPKI_LOWER.flatten(),
        'dpki_upper': DPKI_UPPER.flatten(),
        'dpki_advantage_lower': (DPKI_LOWER - PKI_AVAIL).flatten(),
        'dpki_advantage_upper': (DPKI_UPPER - PKI_AVAIL).flatten()
    }
    df = pd.DataFrame(data_dict)
    df.to_csv('availability_3d_surface_data_responding.csv', index=False)
    
    np.savez('surface_data_matrices_responding.npz', 
             PF=PF, TS=TS, PKI_AVAIL=PKI_AVAIL, DPKI_LOWER=DPKI_LOWER, DPKI_UPPER=DPKI_UPPER,
             pf_values=pf_values, ts_values=ts_values)
    
    print("数据已保存到:")
    print("- availability_3d_surface_data_responding.csv")
    print("- surface_data_matrices_responding.npz")
    print("'Nodes Not Responding'场景数据生成完成！")

if __name__ == '__main__':
    generate_responding_data()