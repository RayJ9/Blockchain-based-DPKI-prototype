# DPKI 'Nodes Not Responding' 场景3D可视化结果

## 项目概述
本项目实现了基于simu5_ava_p场景的"Nodes Not Responding"情况下的DPKI上界面与PKI面的交线计算和3D可视化。

## 场景差异说明

### 当前场景 vs Responding场景
- **当前场景（Malicious）**: 基于simu6.py，考虑恶意节点攻击的情况
- **Responding场景**: 基于simu5_ava_p.py，考虑节点无响应的情况

### 主要计算差异
1. **PKI可用性计算**:
   - Responding场景: `Fi = min(pf + pf * (1 - pf) * (1 - p) * epsilon, 1.0)`
   - 考虑节点失效和无响应的复合影响

2. **DPKI可用性计算**:
   - 使用`calculate_availability_dpki_responding`函数
   - 明确处理k=0（无服务器工作）的情况，可用性设为0
   - 分别计算离线和在线请求的失效概率

## 文件说明

### 核心文件
- `generate_data_responding.py` - 数据生成脚本，基于simu5_ava_p场景
- `plot_3d_matlab_responding.m` - MATLAB 3D可视化脚本
- `surface_data_matrices_responding.npz` - 3D表面数据文件
- `surface_data_matrices_responding.mat` - MATLAB格式数据文件

### 输出文件
- `figure10_dpki_3d_responding.fig` - MATLAB图形文件
- `figure10_dpki_3d_responding.png` - PNG格式图片
- `figure10_dpki_3d_responding.eps` - EPS格式矢量图
- `availability_3d_surface_data_responding.csv` - CSV格式数据

## 技术参数

### 基础参数（与simu5_ava_p一致）
```
lambd: 3.0      # 请求到达率
p: 0.1          # 恶意请求比例
q: 0.3          # PKI处理恶意请求的概率
mu: 7.5         # 服务率
gamma: 0.3      # DPKI检测恶意请求的概率
epsilon: 0.1    # 错误率
lambda_p: 10    # 额外参数
m: 24           # 服务器数量
```

### 网格设置
- **pf范围**: 0 - 1.0 (50个点)
- **ts范围**: 0.5 - 1.5 (50个点)
- **总计算点**: 2500个点

## 交线计算结果

### 成功指标
- **交线点数**: 50个点
- **ts覆盖范围**: 0.5 - 1.5
- **pf集中区域**: 0.2041附近
- **平均最小差值**: 0.22357

### 可视化特性
- PKI面：半透明橙色
- DPKI上界：蓝色线框
- DPKI下界：橙色线框
- DPKI区域：半透明蓝色填充
- 交线：紫色细线（LineWidth=2）

## 场景对比

| 特性 | Malicious场景 | Responding场景 |
|------|---------------|----------------|
| 基础脚本 | simu6.py | simu5_ava_p.py |
| 主要考虑 | 恶意攻击 | 节点无响应 |
| 交线点数 | 50个 | 50个 |
| 平均差值 | 0.0035 | 0.22357 |
| pf集中区域 | 0.4694 | 0.2041 |

## 运行方法
```bash
# 生成数据
python generate_data_responding.py

# 生成3D可视化
matlab -batch "plot_3d_matlab_responding"
```

## 创建时间
2025年10月22日

## 技术特点
- 完全基于simu5_ava_p的计算逻辑
- 与原场景相同的可视化风格
- 高质量的交线计算和绘制
- 完整的数据保存和文档记录