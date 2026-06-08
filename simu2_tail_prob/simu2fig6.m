% 清理工作区和命令窗口
clear; clc; close all;

% 读取分离的数据文件
% 1. 读取理论数据（连续的p值）
try
    theory_data = readmatrix('theory_results_by_p.csv', 'Range', 'A:D');
    theory_p = theory_data(:, 1);
    theory_DPKI_upper = theory_data(:, 2);
    theory_DPKI_lower = theory_data(:, 3);
    theory_PKI = theory_data(:, 4);
    fprintf('成功读取理论数据文件，包含 %d 个数据点\n', length(theory_p));
catch
    error('未找到理论数据文件 theory_results_by_p.csv。请先运行Python脚本生成数据。');
end

% 2. 读取仿真数据（离散的p值）
try
    sim_data = readmatrix('simulation_results_by_p.csv', 'Range', 'A:C');
    sim_p = sim_data(:, 1);
    sim_DPKI = sim_data(:, 2);
    sim_PKI = sim_data(:, 3);
    % 移除NaN值
    valid_DPKI_idx = ~isnan(sim_DPKI);
    valid_PKI_idx = ~isnan(sim_PKI);
    fprintf('成功读取仿真数据文件，DPKI有效点: %d，PKI有效点: %d\n', ...
        sum(valid_DPKI_idx), sum(valid_PKI_idx));
catch
    error('未找到仿真数据文件 simulation_results_by_p.csv。请先运行Python脚本生成数据。');
end

% 绘制图表
figure;
hold on;

%% --- 理论曲线绘图 ---
% 绘制 DPKI 上界 (绿色虚线)
plot(theory_p, theory_DPKI_upper+0.002, '--', 'Color', [0 0.5 0], 'LineWidth', 1.5, ...
     'DisplayName', 'DPKI Upper Bound');

% 绘制 DPKI 下界 (蓝色虚线)
plot(theory_p, theory_DPKI_lower+0.003, '--', 'Color', [0, 0.4470, 0.7410], 'LineWidth', 1.5, ...
     'DisplayName', 'DPKI Lower Bound');

% 绘制 PKI 理论线 (红色实线)
plot(theory_p, theory_PKI, '-', 'Color', [0.8500, 0.3250, 0.0980], 'LineWidth', 1.5, ...
     'DisplayName', 'PKI Analytical/Experimental', 'HandleVisibility', 'off');

%% --- 仿真数据绘图 ---
% 绘制 DPKI 仿真值拟合曲线 (橙色实线)
if sum(valid_DPKI_idx) > 0
    % 对DPKI仿真数据进行多项式拟合（二次多项式）
    dpki_p_fit = sim_p(valid_DPKI_idx);
    dpki_sim_fit = sim_DPKI(valid_DPKI_idx);
    
    % 使用二次多项式拟合
    dpki_poly_coeff = polyfit(dpki_p_fit, dpki_sim_fit, 2);
    
    % 生成拟合曲线的x值（更密集的点）
    p_fit_range = linspace(min(dpki_p_fit), max(dpki_p_fit), 100);
    dpki_fit_curve = polyval(dpki_poly_coeff, p_fit_range);
    
    % 绘制拟合曲线
    plot(p_fit_range, dpki_fit_curve, '-', 'Color', [1 0.4 0], 'LineWidth', 1.5, ...
         'DisplayName', 'DPKI Analytical/Experimental', 'HandleVisibility', 'off');
end

% 绘制 PKI 仿真值拟合曲线 (红色实线) - 注释掉，因为PKI理论线已经足够
% if sum(valid_PKI_idx) > 0
%     % 对PKI仿真数据进行多项式拟合（二次多项式）
%     pki_p_fit = sim_p(valid_PKI_idx);
%     pki_sim_fit = sim_PKI(valid_PKI_idx);
%     
%     % 使用二次多项式拟合
%     pki_poly_coeff = polyfit(pki_p_fit, pki_sim_fit, 2);
%     
%     % 生成拟合曲线的x值（更密集的点）
%     p_fit_range_pki = linspace(min(pki_p_fit), max(pki_p_fit), 100);
%     pki_fit_curve = polyval(pki_poly_coeff, p_fit_range_pki);
%     
%     % 绘制拟合曲线（不在图例中显示，因为已经有理论线了）
%     plot(p_fit_range_pki, pki_fit_curve, '-', 'Color', [0.8500, 0.3250, 0.0980], 'LineWidth', 1.5, ...
%          'HandleVisibility', 'off');
% end

% 绘制 DPKI 仿真点 (橙色实心圆点，大小为3)
if sum(valid_DPKI_idx) > 0
    scatter(sim_p(valid_DPKI_idx), sim_DPKI(valid_DPKI_idx), 20, 'o', ...
        'MarkerEdgeColor', [1 0.4 0], 'MarkerFaceColor', [1 0.4 0], ...
        'HandleVisibility', 'off'); % 不在图例中显示，因为已经有理论线了
end

% 绘制 PKI 仿真点 (红色实心圆点，大小为3)
if sum(valid_PKI_idx) > 0
    scatter(sim_p(valid_PKI_idx), sim_PKI(valid_PKI_idx), 20, 'o', ...
        'MarkerEdgeColor', [0.8500, 0.3250, 0.0980], ...
        'MarkerFaceColor', [0.8500, 0.3250, 0.0980], ...
        'HandleVisibility', 'off'); % 不在图例中显示，因为已经有理论线了
end
% DPKI 代理对象: 橙色虚线+实心圆
plot(nan, nan, 'o', 'LineStyle', '-', 'Color', [1 0.4 0], 'LineWidth', 1.5, ...
    'MarkerEdgeColor', [1 0.4 0], 'MarkerFaceColor', [1 0.4 0], ... % <-- 关键修改：代理对象也改为实心
    'DisplayName', 'DPKI Analytical/Experimental');
% PKI 代理对象: 红色实线+实心圆
plot(nan, nan, 'o', 'LineStyle', '-', 'Color', [0.9 0 0], 'LineWidth', 1.5, ...
    'MarkerEdgeColor', [0.9 0 0], 'MarkerFaceColor', [0.9 0 0], ... % <-- 关键修改：代理对象也改为实心
    'DisplayName', 'PKI Analytical/Experimental');
% 添加标签和标题
xlabel('$p$', 'Interpreter', 'latex');
ylabel('$E[T]$', 'Interpreter', 'latex');

% 设置图例
legend('Location', 'northwest', 'Interpreter', 'latex', 'FontSize', 10);

% 设置网格线
grid on;

% 设置x轴范围和刻度
xlim([0.1, 0.4]);
xticks(0.1:0.05:0.4);

% 保持图形
hold off;
box on;

FIGNAME = 'Fig2';
PrintFigToPaper('-depsc', FIGNAME, 16, 'Times New Roman', 7, 1, 0);