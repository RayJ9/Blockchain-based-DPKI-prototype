%% PKI vs DPKI 系统可用性 3D 切面图 - MATLAB版本
% 基于Python版本simu8.py的MATLAB实现
% 生成与Python版本相同的3D切面可视化效果

clear; clc; close all;

%% ========================================================================
%% SECTION 1: 核心数学函数
%% ========================================================================

% Erlang-C概率计算函数
function prob = erlang_c_probability(m, rho)
    if m == 0
        prob = 1.0;
        return;
    end
    if rho >= 1
        prob = 1.0;
        return;
    end
    
    m_rho = m * rho;
    try
        m_int = floor(m);
        sum_part = 0;
        for i = 0:(m_int-1)
            sum_part = sum_part + (m_rho^i) / factorial(i);
        end
        numerator = (m_rho^m_int) / factorial(m_int) * (1.0 / (1.0 - rho));
        denom = sum_part + numerator;
        if denom > 0
            prob = numerator / denom;
        else
            prob = 0.0;
        end
    catch
        prob = 1.0;
    end
end

% PKI平均延迟计算函数
function latency = get_mean_latency_pki(lambd, p, q, mu, m, epsilon)
    lam_per_server = lambd / m;
    rho = (lam_per_server / mu) * (p / q + (1 - p));
    if rho >= 1
        latency = inf;
        return;
    end
    
    % PKI等待时间计算
    stability_check = q * mu - p * lam_per_server - (1 - p) * q * lam_per_server;
    if stability_check <= 0
        latency = inf;
        return;
    end
    
    num_Wq = (lam_per_server / (q * mu)) * (p + (1 - p) * q^2);
    E_Wq = num_Wq / stability_check;
    
    E_S = p / (q * mu) + (1 - p) / mu;
    extra_delay = 3 * (1 - p) * epsilon * (1 / mu);
    latency = E_Wq + E_S + extra_delay;
end

% DPKI下界延迟计算函数
function latency = get_mean_latency_dpki_lower(lambd, p, q, mu, m, gamma, epsilon)
    lambda_off = lambd * (1 - p) * (1 - gamma) * (1 - epsilon);
    if m > 0
        rho_off = lambda_off / (m * mu);
    else
        rho_off = inf;
    end
    
    if rho_off >= 1
        latency = inf;
        return;
    end
    
    C = erlang_c_probability(m, rho_off);
    if (1 - rho_off) > 0 && m > 0
        E_T_off = C / (m * mu * (1 - rho_off)) + 1 / mu;
    else
        E_T_off = inf;
    end
    
    lambda_on = lambd * (p + (1 - p) * gamma + (1 - p) * (1 - gamma) * epsilon);
    if lambda_on == 0
        E_T_on = 0;
    else
        p_n = (p * lambd) / lambda_on;
        
        % PKI等待时间计算
        stability_check = q * mu - p_n * lambda_on - (1 - p_n) * q * lambda_on;
        if stability_check <= 0
            latency = inf;
            return;
        end
        
        num_Wq = (lambda_on / (q * mu)) * (p_n + (1 - p_n) * q^2);
        E_Wq_on = num_Wq / stability_check;
        E_S_on = p_n / (q * mu) + (1 - p_n) / mu;
        E_T_on = E_Wq_on + E_S_on;
    end
    
    if lambd > 0
        w_on = lambda_on / lambd;
        w_off = lambda_off / lambd;
    else
        w_on = 0;
        w_off = 0;
    end
    
    latency = w_on * E_T_on + w_off * E_T_off;
end

% DPKI上界延迟计算函数
function latency = get_mean_latency_dpki_upper(lambd, p, q, mu, m, gamma, lambda_p, epsilon)
    lambda_off = lambd * (1 - p) * (1 - gamma) * (1 - epsilon);
    if m > 0
        rho_off = lambda_off / (m * mu);
    else
        rho_off = inf;
    end
    
    if rho_off >= 1
        latency = inf;
        return;
    end
    
    C = erlang_c_probability(m, rho_off);
    if (1 - rho_off) > 0 && m > 0
        E_T_off = C / (m * mu * (1 - rho_off)) + 1 / mu;
    else
        E_T_off = inf;
    end
    
    lambda_on = lambd * (p + (1 - p) * gamma + (1 - p) * (1 - gamma) * epsilon);
    if lambda_on == 0
        E_T_on = 0;
    else
        p_n = (p * lambd) / lambda_on;
        rho_on_overall = lambda_on * (p_n / (q * mu) + (1 - p_n) / mu);
        if rho_on_overall >= 1
            latency = inf;
            return;
        end
        
        E_T_b1 = 1 / lambda_p;
        E_B = lambda_on / lambda_p;
        E_B2 = E_B^2 + E_B * (1 + lambda_on / lambda_p);
        E_Si = p_n / (q * mu) + (1 - p_n) / mu;
        Var_Si = (p_n * 2 / ((q * mu)^2) + (1 - p_n) * 2 / (mu^2)) - E_Si^2;
        E_S_block2 = E_B * Var_Si + E_B2 * (E_Si^2);
        rho_block_queue = lambda_p * E_B * E_Si;
        
        if rho_block_queue >= 1
            latency = inf;
            return;
        end
        
        E_W_block = (lambda_p * E_S_block2) / (2 * (1 - rho_block_queue));
        if E_B > 0
            E_S_req = E_Si * E_B2 / E_B;
        else
            E_S_req = 0;
        end
        E_T_on = E_T_b1 + E_W_block + E_S_req;
    end
    
    if lambd > 0
        w_on = lambda_on / lambd;
        w_off = lambda_off / lambd;
    else
        w_on = 0;
        w_off = 0;
    end
    
    latency = w_on * E_T_on + w_off * E_T_off;
end

% Lundberg方程求解函数
function eta = solve_lundberg_equation(lam, pr, q, mu)
    % 定义Lundberg方程
    lundberg_eq = @(eta) eta - lam * (pr * (q * mu / (q * mu - eta)) + (1 - pr) * (mu / (mu - eta)) - 1);
    
    % 求解范围
    upper_bound = min(mu, q * mu) - 1e-9;
    
    try
        eta = fzero(lundberg_eq, [1e-9, upper_bound]);
    catch
        eta = NaN;
    end
end

% 尾概率计算函数
function tail_prob = get_tail_prob_on_chain(ts, model_type, params)
    % 根据模型类型选择延迟函数
    if strcmp(model_type, 'pki')
        E_T = get_mean_latency_pki(params.lambd, params.p, params.q, params.mu, params.m, params.epsilon);
        lam = params.lambd / params.m;
        pr = params.p;
    elseif strcmp(model_type, 'dpki_lower')
        E_T = get_mean_latency_dpki_lower(params.lambd, params.p, params.q, params.mu, params.m, params.gamma, params.epsilon);
        lam = params.lambd * (params.p + (1 - params.p) * params.gamma + (1 - params.p) * (1 - params.gamma) * params.epsilon);
        if lam == 0
            tail_prob = 0.0;
            return;
        end
        pr = (params.p * params.lambd) / lam;
    elseif strcmp(model_type, 'dpki_upper')
        E_T = get_mean_latency_dpki_upper(params.lambd, params.p, params.q, params.mu, params.m, params.gamma, params.lambda_p, params.epsilon);
        lam = params.lambd * (params.p + (1 - params.p) * params.gamma + (1 - params.p) * (1 - params.gamma) * params.epsilon);
        if lam == 0
            tail_prob = 0.0;
            return;
        end
        pr = (params.p * params.lambd) / lam;
    end
    
    if E_T == inf || E_T > 1e6
        tail_prob = 1.0;
        return;
    end
    
    eta = solve_lundberg_equation(lam, pr, params.q, params.mu);
    if isnan(eta)
        tail_prob = 1.0;
        return;
    end
    
    alpha = eta * E_T;
    Ft = alpha * exp(-eta * ts);
    tail_prob = min(Ft, 1.0);
end

%% ========================================================================
%% SECTION 2: 可用性计算函数
%% ========================================================================

% 二项式概率计算
function prob = binomial_prob(n, k, p)
    if k < 0 || k > n
        prob = 0;
        return;
    end
    prob = nchoosek(n, k) * (p^k) * ((1 - p)^(n - k));
end

% PKI可用性计算
function availability = calculate_availability_pki(pf, ts, params)
    Fi = min(pf + pf * (1 - pf) * (1 - params.p) * params.epsilon, 1.0);
    Ft = get_tail_prob_on_chain(ts, 'pki', params);
    availability = (1 - Fi) * (1 - Ft);
end

% DPKI恶意节点场景可用性计算
function [avail_lower, avail_upper] = calculate_availability_dpki_malicious(pf, ts, p_th, params)
    avail_lower = 0.0;
    avail_upper = 0.0;
    total_m = params.m;
    k_threshold = ceil(total_m * p_th);
    
    % 预计算不依赖于k的组件
    lambda_a = params.lambd * (1 - params.p) * (1 - params.gamma) * (1 - params.epsilon);
    lambda_b = params.lambd - lambda_a;
    
    % 对k=0到m个恶意节点求和
    for k = 0:total_m
        % 恰好有k个恶意节点的概率
        prob_k_malicious = binomial_prob(total_m, k, pf);
        
        % 给定k个恶意节点的可用性
        if k >= k_threshold
            avail_k_lower = 0.0;
            avail_k_upper = 0.0;
        else
            % 计算此状态的新有效负载
            if total_m > 0
                extra_load = (k / total_m) * lambda_a;
            else
                extra_load = 0;
            end
            
            lambda_b_prime = lambda_b + extra_load;
            if lambda_b > 0
                scaling_factor = lambda_b_prime / lambda_b;
            else
                scaling_factor = 1.0;
            end
            
            mod_params = params;
            mod_params.lambd = params.lambd * scaling_factor;
            
            % 计算此特定状态k的Ft
            Ft_lower = get_tail_prob_on_chain(ts, 'dpki_lower', mod_params);
            Ft_upper = get_tail_prob_on_chain(ts, 'dpki_upper', mod_params);
            
            avail_k_lower = 1 - Ft_lower;
            avail_k_upper = 1 - Ft_upper;
        end
        
        % 添加到总期望可用性
        avail_lower = avail_lower + prob_k_malicious * avail_k_lower;
        avail_upper = avail_upper + prob_k_malicious * avail_k_upper;
    end
end

%% ========================================================================
%% SECTION 3: 主程序 - 3D切面图可视化
%% ========================================================================

fprintf('--- 开始计算系统可用性A受pf和M同时影响的分析 ---\n');

% 1. 设置参数范围
PF_VALUES = linspace(0.0, 1.0, 30);  % 从0.0到1.0
M_VALUES = [4, 5, 6, 7, 8];  % 5个M值

% 固定其他参数
BASE_PARAMS.p = 0.1;
BASE_PARAMS.q = 0.3;
BASE_PARAMS.mu = 7.5;
BASE_PARAMS.gamma = 0.1;
BASE_PARAMS.epsilon = 0.1;
BASE_PARAMS.lambda_p = 10;

% 固定λ和其他参数
FIXED_LAMBDA = 2.0;  % 固定总到达率为2.0
TIMEOUT_THRESHOLD_TS = 0.6;
CONSENSUS_THRESHOLD_P_TH = 0.5;

fprintf('pf范围: %.1f - %.1f\n', min(PF_VALUES), max(PF_VALUES));
fprintf('M范围: %d - %d\n', min(M_VALUES), max(M_VALUES));
fprintf('固定参数: λ=%.1f, ts=%.1f, p_th=%.1f\n', FIXED_LAMBDA, TIMEOUT_THRESHOLD_TS, CONSENSUS_THRESHOLD_P_TH);

% 2. 计算可用性数据
results = [];
total_combinations = length(PF_VALUES) * length(M_VALUES);
current_count = 0;

for i = 1:length(PF_VALUES)
    pf = PF_VALUES(i);
    for j = 1:length(M_VALUES)
        m = M_VALUES(j);
        current_count = current_count + 1;
        
        if mod(current_count, 50) == 0
            fprintf('进度: %d/%d (%.1f%%)\n', current_count, total_combinations, 100*current_count/total_combinations);
        end
        
        % 设置当前参数
        current_params = BASE_PARAMS;
        current_params.lambd = FIXED_LAMBDA;
        current_params.m = m;
        
        % 计算PKI可用性
        try
            avail_pki = calculate_availability_pki(pf, TIMEOUT_THRESHOLD_TS, current_params);
        catch
            avail_pki = 0.0;
        end
        
        % 计算DPKI可用性
        try
            [dpki_lower, dpki_upper] = calculate_availability_dpki_malicious(pf, TIMEOUT_THRESHOLD_TS, CONSENSUS_THRESHOLD_P_TH, current_params);
        catch
            dpki_lower = 0.0;
            dpki_upper = 0.0;
        end
        
        % 存储结果
        result.pf = pf;
        result.m = m;
        result.PKI = avail_pki;
        result.DPKI_Lower = dpki_lower;
        result.DPKI_Upper = dpki_upper;
        result.DPKI_Mean = (dpki_lower + dpki_upper) / 2;
        
        results = [results; result];
    end
end

fprintf('计算完成！\n');

% 3. 创建3D切面图
figure('Position', [100, 100, 1200, 900]);

% 设置颜色映射
colors_pki = colormap(hot(length(M_VALUES)));
colors_dpki = colormap(cool(length(M_VALUES)));

% 创建3D图形
hold on;

% 为每个M值创建切面
for i = 1:length(M_VALUES)
    m = M_VALUES(i);
    
    % 提取当前M值的数据
    m_indices = [results.m] == m;
    m_data = results(m_indices);
    
    % 按pf排序
    [~, sort_idx] = sort([m_data.pf]);
    m_data = m_data(sort_idx);
    
    pf_vals = [m_data.pf];
    pki_vals = [m_data.PKI];
    dpki_vals = [m_data.DPKI_Mean];
    
    % 创建网格用于平面
    pf_mesh = repmat(pf_vals, 2, 1);
    m_mesh = repmat(m, size(pf_mesh));
    
    % 添加淡灰色背景平面
    white_mesh = zeros(size(pf_mesh));
    surf(pf_mesh, m_mesh, white_mesh, 'FaceColor', [0.8, 0.8, 0.8], 'FaceAlpha', 0.3, 'EdgeColor', 'none');
    
    % 添加PKI平面
    pki_mesh = repmat(pki_vals, 2, 1);
    surf(pf_mesh, m_mesh, pki_mesh, 'FaceColor', colors_pki(i,:), 'FaceAlpha', 0.7, 'EdgeColor', 'none');
    
    % 添加DPKI平面（轻微偏移）
    dpki_mesh = repmat(dpki_vals, 2, 1);
    m_mesh_dpki = m_mesh + 0.05;
    surf(pf_mesh, m_mesh_dpki, dpki_mesh, 'FaceColor', colors_dpki(i,:), 'FaceAlpha', 0.7, 'EdgeColor', 'none');
    
    % 添加轮廓线
    plot3(pf_vals, repmat(m, size(pf_vals)), pki_vals, 'Color', colors_pki(i,:), 'LineWidth', 2.5);
    plot3(pf_vals, repmat(m+0.05, size(pf_vals)), dpki_vals, 'Color', colors_dpki(i,:), 'LineWidth', 2.5, 'LineStyle', '--');
end

% 设置坐标轴
xlabel('恶意节点概率 pf', 'FontSize', 14);
ylabel('服务CA数量 M', 'FontSize', 14);
zlabel('系统可用性 A', 'FontSize', 14);
title(sprintf('PKI vs DPKI 系统可用性 3D 切面图\n(λ=%.1f)', FIXED_LAMBDA), 'FontSize', 16, 'FontWeight', 'bold');

% 设置坐标轴范围
xlim([min(PF_VALUES), max(PF_VALUES)]);
ylim([min(M_VALUES)-0.5, max(M_VALUES)+0.5]);
zlim([0, 1]);

% 添加图例
legend({'', 'PKI', 'DPKI'}, 'Location', 'northwest', 'FontSize', 12);

% 设置视角
view(45, 25);

% 移除网格和背景
grid off;
set(gca, 'XColor', 'k', 'YColor', 'k', 'ZColor', 'k');

hold off;

% 4. 保存图形和数据
saveas(gcf, 'availability_pf_m_slices_3d_matlab.png');
fprintf('3D切面图已保存为: availability_pf_m_slices_3d_matlab.png\n');

% 保存数据到CSV文件
data_table = struct2table(results);
writetable(data_table, 'availability_pf_m_slices_3d_data_matlab.csv');
fprintf('数据已保存为: availability_pf_m_slices_3d_data_matlab.csv\n');

% 5. 显示关键统计信息
fprintf('\n=== 关键统计信息 ===\n');
pki_vals = [results.PKI];
dpki_vals = [results.DPKI_Mean];

fprintf('PKI最大可用性: %.4f\n', max(pki_vals));
fprintf('PKI最小可用性: %.4f\n', min(pki_vals));
fprintf('DPKI最大可用性: %.4f\n', max(dpki_vals));
fprintf('DPKI最小可用性: %.4f\n', min(dpki_vals));

% 找到最优配置
[~, best_pki_idx] = max(pki_vals);
[~, best_dpki_idx] = max(dpki_vals);

fprintf('\nPKI最优配置: pf=%.2f, M=%d, A=%.4f\n', results(best_pki_idx).pf, results(best_pki_idx).m, results(best_pki_idx).PKI);
fprintf('DPKI最优配置: pf=%.2f, M=%d, A=%.4f\n', results(best_dpki_idx).pf, results(best_dpki_idx).m, results(best_dpki_idx).DPKI_Mean);

fprintf('\n程序执行完成！\n');