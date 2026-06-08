% =========================================================================
% SIMU5 3D Visualization Script - "Nodes Not Responding" Scenario
% 基于simu5_ava_p.py的计算方法，使用与simu8相同的可视化风格
% =========================================================================

clear; clc; close all;

fprintf('--- 开始基于SIMU5方法生成3D切面图 ---\n');

% =========================================================================
% SECTION 1: HELPER FUNCTIONS (从simu5_ava_p.py移植)
% =========================================================================

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

function latency = get_mean_latency_pki(lambd, p, q, mu, m, epsilon)
    lam_per_server = lambd / m;
    rho = (lam_per_server / mu) * (p / q + (1 - p));
    if rho >= 1
        latency = inf;
        return;
    end
    
    % PKI wait time calculation
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

function latency = get_mean_latency_dpki_lower(lambd, p, q, mu, m, gamma, epsilon)
    lambda_off = lambd * (1 - p) * (1 - gamma) * (1 - epsilon);
    rho_off = lambda_off / (m * mu);
    if rho_off >= 1 || m <= 0
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
        
        % PKI wait time for on-chain
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
    
    w_on = lambda_on / lambd;
    w_off = lambda_off / lambd;
    latency = w_on * E_T_on + w_off * E_T_off;
end

function latency = get_mean_latency_dpki_upper(lambd, p, q, mu, m, gamma, lambda_p, epsilon)
    lambda_off = lambd * (1 - p) * (1 - gamma) * (1 - epsilon);
    rho_off = lambda_off / (m * mu);
    if rho_off >= 1 || m <= 0
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
        E_S_req = E_Si * E_B2 / E_B;
        if E_B <= 0
            E_S_req = 0;
        end
        E_T_on = E_T_b1 + E_W_block + E_S_req;
    end
    
    w_on = lambda_on / lambd;
    w_off = lambda_off / lambd;
    latency = w_on * E_T_on + w_off * E_T_off;
end

function prob = binomial_prob(n, k, p)
    if k < 0 || k > n
        prob = 0;
        return;
    end
    prob = nchoosek(n, k) * (p^k) * ((1-p)^(n-k));
end

function prob = get_tail_prob_M_M_m(ts, lambda_a, mu, m)
    if m <= 0
        prob = 1.0;
        return;
    end
    
    rho = lambda_a / (m * mu);
    if rho >= 1
        prob = 1.0;
        return;
    end
    
    C_m_rho = erlang_c_probability(m, rho);
    term1 = mu * (m - 1) - lambda_a;
    
    if abs(term1) < 1e-9
        prob = (C_m_rho * mu * ts + 1) * exp(-mu * ts);
    else
        factor = (mu * C_m_rho) / term1;
        term2 = 1 - exp(-term1 * ts);
        prob = exp(-mu * ts) + factor * term2;
    end
    
    prob = min(prob, 1.0);
end

function avail = calculate_availability_pki(pf, ts, params)
    Fi = min(pf + pf * (1 - pf) * (1 - params.p) * params.epsilon, 1.0);
    
    % 简化的tail probability计算 (基于平均延迟的指数近似)
    E_T = get_mean_latency_pki(params.lambd, params.p, params.q, params.mu, params.m, params.epsilon);
    if E_T == inf || E_T > 1e6
        Ft = 1.0;
    else
        % 使用指数分布近似
        Ft = exp(-ts / E_T);
    end
    
    avail = (1 - Fi) * (1 - Ft);
end

function [avail_lower, avail_upper] = calculate_availability_dpki_responding(pf, ts, params)
    total_m = params.m;
    lambda_a = params.lambd * (1 - params.p) * (1 - params.gamma) * (1 - params.epsilon);
    lambda_b = params.lambd - lambda_a;
    
    % 使用正确的DPKI上下界延迟计算函数
    E_T_lower = get_mean_latency_dpki_lower(params.lambd, params.p, params.q, params.mu, params.m, params.gamma, params.epsilon);
    E_T_upper = get_mean_latency_dpki_upper(params.lambd, params.p, params.q, params.mu, params.m, params.gamma, params.lambda_p, params.epsilon);
    
    % 下界：使用下界延迟计算失败概率
    if E_T_lower == inf || E_T_lower > 1e6
        fail_prob_on_lower = 1.0;
    else
        fail_prob_on_lower = exp(-ts / E_T_lower);
    end
    fail_prob_on_lower = (lambda_b / params.lambd) * fail_prob_on_lower;
    
    % 上界：使用上界延迟计算失败概率
    if E_T_upper == inf || E_T_upper > 1e6
        fail_prob_on_upper = 1.0;
    else
        fail_prob_on_upper = exp(-ts / E_T_upper);
    end
    fail_prob_on_upper = (lambda_b / params.lambd) * fail_prob_on_upper;
    
    avail_lower = 0.0;
    avail_upper = 0.0;
    
    for k = 0:total_m
        prob_k_servers = binomial_prob(total_m, k, 1 - pf);
        
        if k == 0
            avail_k_lower = 0.0;
            avail_k_upper = 0.0;
        else
            fail_prob_off_given_k = (lambda_a / params.lambd) * get_tail_prob_M_M_m(ts, lambda_a, params.mu, k);
            avail_k_lower = 1 - fail_prob_off_given_k - fail_prob_on_lower;
            avail_k_upper = 1 - fail_prob_off_given_k - fail_prob_on_upper;
        end
        
        avail_lower = avail_lower + prob_k_servers * avail_k_lower;
        avail_upper = avail_upper + prob_k_servers * avail_k_upper;
    end
end

% =========================================================================
% SECTION 2: 参数设置 (与simu8保持相同的数值范围)
% =========================================================================

% 基础参数 (来自simu5)
BASE_PARAMS = struct();
BASE_PARAMS.lambd = 3.0;
BASE_PARAMS.p = 0.1;
BASE_PARAMS.q = 0.3;
BASE_PARAMS.mu = 7.5;
BASE_PARAMS.gamma = 0.3;
BASE_PARAMS.epsilon = 0.1;
BASE_PARAMS.lambda_p = 10;

TIMEOUT_THRESHOLD_TS = 0.6;

% 与simu8相同的数值范围
unique_pf = linspace(0, 1, 30);  % pf范围: 0-1, 30个点
unique_m = 4:12;                 % M范围: 4-12, 9个值

fprintf('pf范围: %.1f - %.1f (%d个点)\n', min(unique_pf), max(unique_pf), length(unique_pf));
fprintf('M范围: %d - %d (%d个值)\n', min(unique_m), max(unique_m), length(unique_m));

% =========================================================================
% SECTION 3: 数据计算
% =========================================================================

fprintf('开始计算可用性数据...\n');

% 存储所有数据
all_data = [];
data_count = 0;

for i = 1:length(unique_pf)
    for j = 1:length(unique_m)
        pf_val = unique_pf(i);
        m_val = unique_m(j);
        
        % 设置当前参数
        current_params = BASE_PARAMS;
        current_params.m = m_val;
        
        % 计算PKI可用性
        pki_availability = calculate_availability_pki(pf_val, TIMEOUT_THRESHOLD_TS, current_params);
        
        % 计算DPKI可用性 (同时保存上界和下界)
        [dpki_lower, dpki_upper] = calculate_availability_dpki_responding(pf_val, TIMEOUT_THRESHOLD_TS, current_params);
        
        % 存储数据 (增加一列用于DPKI上界)
        data_count = data_count + 1;
        all_data(data_count, :) = [pf_val, m_val, pki_availability, dpki_lower, dpki_upper];
    end
end

fprintf('数据计算完成，共%d个数据点\n', data_count);

% =========================================================================
% SECTION 4: 3D可视化 (严格按照simu8_visualization.m的风格)
% =========================================================================

fprintf('开始生成3D可视化...\n');

% 创建图形窗口
figure('Position', [100, 100, 1200, 900]);
hold on;

% 设置背景颜色
BACKGROUND_COLOR = [0.9, 0.9, 0.9];
set(gcf, 'Color', BACKGROUND_COLOR);

% 定义颜色（与simu8完全相同）
PKI_COLOR = [0.85, 0.325, 0.098];     % 橙红色
DPKI_COLOR = [0.0, 0.447, 0.741];     % 蓝色

% 提取数据
pf_values = all_data(:, 1);
m_values = all_data(:, 2);
pki_values = all_data(:, 3);
dpki_lower_values = all_data(:, 4);
dpki_upper_values = all_data(:, 5);

% 获取唯一值
unique_pf = unique(pf_values);
unique_m = unique(m_values);

%% ========================================================================
%% 绘制3D数据点和连接线（与simu8完全相同的风格）
%% ========================================================================

% 为每个M值绘制PKI和DPKI的线条
for j = 1:length(unique_m)
    m_val = unique_m(j);
    
    % 提取当前M值的数据
    current_indices = (m_values == m_val);
    current_pf = pf_values(current_indices);
    current_pki = pki_values(current_indices);
    current_dpki_lower = dpki_lower_values(current_indices);
    current_dpki_upper = dpki_upper_values(current_indices);
    
    % 按pf值排序
    [sorted_pf, sort_idx] = sort(current_pf);
    sorted_pki = current_pki(sort_idx);
    sorted_dpki_lower = current_dpki_lower(sort_idx);
    sorted_dpki_upper = current_dpki_upper(sort_idx);
    
    % 绘制PKI线条（实线，无点标记）
     if j == 1
         % 只在第一条线上添加图例
         plot3(sorted_pf, repmat(m_val, size(sorted_pf)), sorted_pki, ...
               'Color', PKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
               'DisplayName', 'PKI');
     else
         plot3(sorted_pf, repmat(m_val, size(sorted_pf)), sorted_pki, ...
               'Color', PKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
               'HandleVisibility', 'off');
     end
     
     % 绘制DPKI下界线条（实线，无点标记）
     if j == 1
         % 只在第一条线上添加图例，合并DPKI上下界为一个图例项
         plot3(sorted_pf, repmat(m_val, size(sorted_pf)), sorted_dpki_lower, ...
               'Color', DPKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
               'DisplayName', 'DPKI');
     else
         plot3(sorted_pf, repmat(m_val, size(sorted_pf)), sorted_dpki_lower, ...
               'Color', DPKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
               'HandleVisibility', 'off');
     end
     
     % 绘制DPKI上界线条（实线，无点标记）
     plot3(sorted_pf, repmat(m_val, size(sorted_pf)), sorted_dpki_upper, ...
           'Color', DPKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
           'HandleVisibility', 'off');
     
     % 在DPKI上下界之间添加平面连接
     for k = 1:length(sorted_pf)-1
         % 创建四边形面片连接相邻的上下界点
         x_quad = [sorted_pf(k), sorted_pf(k+1), sorted_pf(k+1), sorted_pf(k)];
         y_quad = [m_val, m_val, m_val, m_val];
         z_quad = [sorted_dpki_lower(k), sorted_dpki_lower(k+1), sorted_dpki_upper(k+1), sorted_dpki_upper(k)];
         
         % 绘制半透明的面片
         patch(x_quad, y_quad, z_quad, DPKI_COLOR, 'FaceAlpha', 0.3, ...
               'EdgeColor', 'none', 'HandleVisibility', 'off');
     end
end

%% ========================================================================
%% 添加投影效果（简化版本，只绘制蓝色投影线）
%% ========================================================================

% 投影到A-M面上 (YZ平面, pf=0)
% 首先绘制投影平面的白色底色
m_range = [min(unique_m), max(unique_m)];
a_range = [0, 1];  % A轴范围恢复为完整的0-1

% 创建投影平面的四个角点
projection_m = [m_range(1), m_range(2), m_range(2), m_range(1)];
projection_pf = [0.0005, 0.0005, 0.0005, 0.0005];  % pf=0.0005平面，稍微往左移动
projection_a = [a_range(1), a_range(1), a_range(2), a_range(2)];

% 绘制白色投影平面底色
fill3(projection_pf, projection_m, projection_a, 'white', ...
      'FaceAlpha', 0.9, 'EdgeColor', 'none', 'HandleVisibility', 'off');

% 为指定的pf值绘制DPKI在A-M面上的投影
selected_pf_values = [0.2, 0.6, 0.8];

for i = 1:length(selected_pf_values)
    target_pf = selected_pf_values(i);
    
    % 找到最接近目标pf值的实际pf值
    [~, closest_idx] = min(abs(unique_pf - target_pf));
    pf = unique_pf(closest_idx);
    
    % 获取当前pf值的数据
    pf_indices = (pf_values == pf);
    current_m = m_values(pf_indices);
    current_dpki_lower = dpki_lower_values(pf_indices);
    current_dpki_upper = dpki_upper_values(pf_indices);
    
    % 在A-M面绘制DPKI下界投影 (pf=0处) - 蓝色虚线
    plot3(zeros(size(current_m)), current_m, current_dpki_lower, ...
          'Color', DPKI_COLOR, 'LineWidth', 1.5, 'LineStyle', '--', ...
          'HandleVisibility', 'off', 'Marker', 'none');
    
    % 在A-M面绘制DPKI上界投影 (pf=0处) - 蓝色虚线
    plot3(zeros(size(current_m)), current_m, current_dpki_upper, ...
          'Color', DPKI_COLOR, 'LineWidth', 1.5, 'LineStyle', '--', ...
          'HandleVisibility', 'off', 'Marker', 'none');
    
    % 在两条投影线之间添加绿色填充 (pf=0处)
    % 创建填充区域的顶点
    fill_x = [zeros(size(current_m)); zeros(size(current_m))];
    fill_y = [current_m; flipud(current_m)];
    fill_z = [current_dpki_lower; flipud(current_dpki_upper)];
    
    % 绘制绿色填充面片
    fill3(fill_x, fill_y, fill_z, [0.0, 0.6, 0.0], ...
          'FaceAlpha', 0.3, 'EdgeColor', 'none', 'HandleVisibility', 'off');
    
    % 添加从3D点到投影点的连接线
    for j = 1:length(current_m)
        % 找到对应的3D点
        m_val = current_m(j);
        dpki_lower_val = current_dpki_lower(j);
        dpki_upper_val = current_dpki_upper(j);
        
        % 绘制从3D下界点到投影点的浅灰色虚线
        plot3([target_pf, 0], [m_val, m_val], [dpki_lower_val, dpki_lower_val], ...
              'Color', [0.7, 0.7, 0.7], 'LineWidth', 1.0, 'LineStyle', '--', ...
              'HandleVisibility', 'off');
        
        % 绘制从3D上界点到投影点的浅灰色虚线
        plot3([target_pf, 0], [m_val, m_val], [dpki_upper_val, dpki_upper_val], ...
              'Color', [0.7, 0.7, 0.7], 'LineWidth', 1.0, 'LineStyle', '--', ...
              'HandleVisibility', 'off');
    end
    
    % 添加pf标签
    % 找到M最大值位置作为标签位置
    [sorted_m, sort_idx] = sort(current_m);
    sorted_dpki_lower = current_dpki_lower(sort_idx);
    max_m = max(sorted_m);
    max_m_idx = find(sorted_m == max_m, 1);
    label_m = sorted_m(max_m_idx);
    label_dpki = sorted_dpki_lower(max_m_idx);  % 使用下界作为标签位置
    
    % 根据pf值调整标签的垂直位置
    if target_pf == 0.2
        label_offset = -0.02;  % pf=0.2 稍微往下一点点
    elseif target_pf == 0.4
        label_offset = 0.02;  % pf=0.4 稍微上方
    elseif target_pf == 0.6
        label_offset = -0.06; % pf=0.6 往下移，放在0.2和0.8中间
    elseif target_pf == 0.8
        label_offset = -0.05; % pf=0.8 在下方
    else
        label_offset = 0;     % 其他值保持默认
    end
    
    % 在投影平面上添加文本标签（放在M最大值右边）
    text(0.05, label_m + 0.5, label_dpki + label_offset, sprintf('pf=%.1f', target_pf), ...
         'FontSize', 10, 'Color', 'black', 'FontName', 'Times New Roman', ...
         'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
end

%% ========================================================================
%% 设置图形属性（严格按照simu8的风格）
%% ========================================================================

% 设置坐标轴
h_xlabel = xlabel('Failure Probability $p_f$', 'Interpreter', 'latex');
h_ylabel = ylabel('Service CA Number $M$', 'Interpreter', 'latex');
zlabel('Availability $A$', 'Interpreter', 'latex');



% 设置坐标轴范围
xlim([min(unique_pf), max(unique_pf)]);
ylim([min(unique_m), max(unique_m)]);  % M轴贴边，去掉0.5的边距
zlim([0, 1]);  % A轴保持完整范围0-1

% 设置轴的显示比例，压缩A轴的视觉高度到50%
pbaspect([1, 1, 0.5]);  % [pf轴, M轴, A轴] 的相对比例

% 反转pf坐标轴，使1在最左边，0在最右边
set(gca, 'XDir', 'reverse');

% 设置Y轴（M轴）只显示4,5,6,7,8,9,10,11,12
set(gca, 'YTick', [4, 5, 6, 7, 8, 9, 10, 11, 12]);

% 添加图例
legend('Location', 'northwest', 'FontSize', 12);

% 设置视角 - 调整以适应1:1长宽比
view(45, 25);

% 在设置视角后调整标签方向，使其在当前视角下与坐标轴平行
% 对于视角(45, 25)，手动调整标签旋转角度
set(h_xlabel, 'Rotation', -25, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');  % x轴标签25度，调整位置离轴近一点
set(h_ylabel, 'Rotation', 25, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');   % y轴标签与y轴平行，调整位置

% 移除网格和背景
grid on;
set(gca, 'XColor', 'k', 'YColor', 'k', 'ZColor', 'k');

% 添加3D框架（除了正对着的边）
box on;
set(gca, 'BoxStyle', 'back');

hold off;

% =========================================================================
% SECTION 5: 保存结果
% =========================================================================

% 保存图形
output_filename = 'availability_pf_m_slices_3d_simu5_unified.png';
saveas(gcf, output_filename, 'png');
fprintf('3D切面图已保存为: %s\n', output_filename);

% 保存数据到CSV
csv_data = array2table(all_data, 'VariableNames', {'pf', 'M', 'PKI_Availability', 'DPKI_Lower', 'DPKI_Upper'});
csv_filename = 'availability_pf_m_slices_3d_data_simu5.csv';
writetable(csv_data, csv_filename);
fprintf('数据已保存为: %s\n', csv_filename);

% 输出统计信息
fprintf('\n=== 关键统计信息 ===\n');
fprintf('PKI最大可用性: %.4f\n', max(all_data(:,3)));
fprintf('PKI最小可用性: %.4f\n', min(all_data(:,3)));
fprintf('DPKI下界最大可用性: %.4f\n', max(all_data(:,4)));
fprintf('DPKI下界最小可用性: %.4f\n', min(all_data(:,4)));
fprintf('DPKI上界最大可用性: %.4f\n', max(all_data(:,5)));
fprintf('DPKI上界最小可用性: %.4f\n', min(all_data(:,5)));

% 找到最优配置
[max_pki, max_pki_idx] = max(all_data(:,3));
[max_dpki_lower, max_dpki_lower_idx] = max(all_data(:,4));
[max_dpki_upper, max_dpki_upper_idx] = max(all_data(:,5));

fprintf('\nPKI最优配置: pf=%.2f, M=%d, A=%.4f\n', ...
        all_data(max_pki_idx,1), all_data(max_pki_idx,2), max_pki);
fprintf('DPKI下界最优配置: pf=%.2f, M=%d, A=%.4f\n', ...
        all_data(max_dpki_lower_idx,1), all_data(max_dpki_lower_idx,2), max_dpki_lower);
fprintf('DPKI上界最优配置: pf=%.2f, M=%d, A=%.4f\n', ...
        all_data(max_dpki_upper_idx,1), all_data(max_dpki_upper_idx,2), max_dpki_upper);

fprintf('\n=== 颜色方案 ===\n');
fprintf('PKI颜色: [%.4f, %.4f, %.4f] (橙红色)\n', PKI_COLOR);
fprintf('DPKI颜色: [%.4f, %.4f, %.4f] (蓝色)\n', DPKI_COLOR);
fprintf('背景颜色: [%.1f, %.1f, %.1f] (淡灰色)\n', BACKGROUND_COLOR);
% Save figure
% FIGNAME = 'Fig6s';
% PrintFigToPaper('-depsc', FIGNAME, 12, 'Times New Roman', 7, 1, 0);
FIGNAME = 'Fig6s';
PrintFigToPaper('-depsc', FIGNAME, 12, 'Times New Roman', 7, 1, 0);

fprintf('\n程序执行完成！\n');