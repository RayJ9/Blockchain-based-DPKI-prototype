% 清理工作区和命令窗口
clear; clc; close all;


data = readmatrix('simulation_lambda.csv', 'Range', 'A:F');

% 提取所需列的数据
epsilon = data(:, 1);
DPKI_upper_theory = data(:, 2);
DPKI_lower_theory = data(:, 3);
sim_results_DPKI = data(:, 4); % 第4列为DPKI实际值
PKI_theory = data(:, 5);
sim_results_PKI = data(:, 6); % 第6列为PKI实际值

% 绘制图表
figure;
hold on;

%% --- 理论曲线绘图 ---
% 绘制 DPKI 上界 (绿色实线)
plot(epsilon, DPKI_upper_theory, '--','Color', [0 0.5 0], 'LineWidth', 1.5, 'DisplayName', 'DPKI Upper Bound');
% 绘制 DPKI 下界 (蓝色实线)
plot(epsilon, DPKI_lower_theory,'--', 'Color', [0, 0.4470, 0.7410], 'LineWidth', 1.5, 'DisplayName', 'DPKI Lower Bound');
% 绘制 PKI 理论直线 (红色实线，不在图例中显示)
plot(epsilon, PKI_theory, 'Color', [0.8500, 0.3250, 0.0980], 'LineWidth', 1.5, 'HandleVisibility', 'off'); 

%% --- DPKI 数据处理与绘图 ---
idx_DPKI = ~isnan(sim_results_DPKI);
fit_x_DPKI = epsilon(idx_DPKI);
fit_y_DPKI = sim_results_DPKI(idx_DPKI);
% 进行二次多项式拟合
p = polyfit(fit_x_DPKI, fit_y_DPKI, 2);
y_fit_DPKI = polyval(p, epsilon);
% 绘制 DPKI 拟合直线 (橙色虚线，不在图例中显示)
plot(epsilon, y_fit_DPKI,  'LineWidth', 1.5, 'Color', [1 0.4 0], 'HandleVisibility', 'off'); 

% 绘制 DPKI 仿真**实心点** (橙色，不在图例中显示)
scatter(fit_x_DPKI, fit_y_DPKI, 20, 'LineWidth', 1.5, ...
    'MarkerEdgeColor', [1 0.4 0], ...
    'MarkerFaceColor', [1 0.4 0], ...  % <-- 关键修改：添加填充色
    'HandleVisibility', 'off'); 

%% --- PKI 数据处理与绘图 ---
idx_PKI = ~isnan(sim_results_PKI);

% 绘制 PKI 仿真**实心点** (红色，不在图例中显示)
scatter(epsilon(idx_PKI), sim_results_PKI(idx_PKI), 20, 'LineWidth', 1.5, ...
    'MarkerEdgeColor', [0.9 0 0], ...
    'MarkerFaceColor', [0.9 0 0], ...  % <-- 关键修改：添加填充色
    'HandleVisibility', 'off'); 

%% --- 图例代理对象创建 ---
% 使用 plot(nan, nan, ...) 创建只用于图例显示的代理图形对象
plot(nan, nan, 'o', 'LineStyle', '-', 'Color', [1 0.4 0], 'LineWidth', 1.5, ...
    'MarkerEdgeColor', [1 0.4 0], 'MarkerFaceColor', [1 0.4 0], ... % <-- 关键修改：代理对象也改为实心
    'DisplayName', 'DPKI Analytical/Experimental');
plot(nan, nan, 'o', 'LineStyle', '-', 'Color', [0.9 0 0], 'LineWidth', 1.5, ...
    'MarkerEdgeColor', [0.9 0 0], 'MarkerFaceColor', [0.9 0 0], ... % <-- 关键修改：代理对象也改为实心
    'DisplayName', 'PKI Analytical/Experimental');

% 添加标签和标题
xlabel('$\epsilon$', 'Interpreter', 'latex');
ylabel('$E[T]$', 'Interpreter', 'latex');

% 设置图例
legend('Location', 'northwest','Interpreter', 'latex', 'FontSize', 10);

% 设置网格线
grid on;

% 保持图形
hold off;
box on;

FIGNAME = 'Fig3';
PrintFigToPaper('-depsc', FIGNAME, 16, 'Times New Roman', 7, 1, 0);