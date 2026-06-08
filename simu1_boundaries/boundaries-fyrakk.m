% 清除工作区和命令窗口
clear;
clc;

% 定义颜色
deep_green = [0 0.5 0];
deep_orange = [1 0.4 0];
deep_blue = [0, 0.4470, 0.7410];

data = readmatrix('boundaries.csv', 'NumHeaderLines', 3);


lambda = data(:, 1);
dpki_lower_theory_2 = data(:, 2);
dpki_sim_2 = data(:, 3);
dpki_upper_theory_2 = data(:, 4);
dpki_sim_4 = data(:, 6);
dpki_upper_theory_4 = data(:, 7);
dpki_sim_6 = data(:, 9);
dpki_upper_theory_6 = data(:, 10);



% 对 lambda 进行加密，以获得更平滑的曲线
lambda_fine = linspace(min(lambda), max(lambda), 200);

% 使用样条插值（spline）来拟合平滑曲线
dpki_lower_theory_2_fit = spline(lambda, dpki_lower_theory_2, lambda_fine);
dpki_sim_2_fit = spline(lambda, dpki_sim_2, lambda_fine);
dpki_upper_theory_2_fit = spline(lambda, dpki_upper_theory_2, lambda_fine);
dpki_sim_4_fit = spline(lambda, dpki_sim_4, lambda_fine);
dpki_upper_theory_4_fit = spline(lambda, dpki_upper_theory_4, lambda_fine);
dpki_sim_6_fit = spline(lambda, dpki_sim_6, lambda_fine);
dpki_upper_theory_6_fit = spline(lambda, dpki_upper_theory_6, lambda_fine);

% 开始绘图
figure;
hold on;
box on;
grid on;

%% 1. 绘制共同下界 (蓝色虚线)
% 保持蓝色虚线作为共同下界，以清晰表达“共同性”
h1 = plot(lambda_fine, dpki_lower_theory_2_fit, 'b--', 'Color', deep_blue,'LineWidth', 1.5);

%% 2. 绘制 lambda_p = 2 的曲线 (深绿)
% 仿真值 (实线)
h2 = plot(lambda_fine, dpki_sim_2_fit, 'Color', deep_green, 'LineWidth', 1.5);
% 仿真点 (仅用于数据点展示，不纳入图例)
plot(lambda, dpki_sim_2, 'o', 'Color', deep_green, 'MarkerFaceColor', deep_green, 'MarkerSize', 4, 'LineWidth', 1.5);
% 上界 (虚线)
h3 = plot(lambda_fine, dpki_upper_theory_2_fit, '--', 'Color', deep_green, 'LineWidth', 1.5);

%% 3. 绘制 lambda_p = 6 的曲线 (深橙)
% 仿真值 (实线)
h4 = plot(lambda_fine, dpki_sim_6_fit, 'Color', deep_orange, 'LineWidth', 1.5);
% 仿真点 (仅用于数据点展示，不纳入图例)
plot(lambda, dpki_sim_6, 'o', 'Color', deep_orange, 'MarkerFaceColor', deep_orange, 'MarkerSize', 4, 'LineWidth', 1.5);
% 上界 (虚线)
h5 = plot(lambda_fine, dpki_upper_theory_6_fit, '--', 'Color', deep_orange, 'LineWidth', 1.5);

% 设置图形标题和坐标轴标签
xlabel('$\lambda$', 'Interpreter', 'latex');
ylabel('$E[T]$', 'Interpreter', 'latex');

% 设置 Y 轴范围以匹配您的原始图像
ylim([0 3]); 

% 使用句柄创建图例，确保顺序和描述完全正确
% 顺序：下界 -> lambda_p=2 仿真 -> lambda_p=2 上界 -> lambda_p=6 仿真 -> lambda_p=6 上界
legend([h1, h2, h3, h4, h5], ...
       'Lower Bound', ...
       '$\lambda_p=2$ (Simulation)', ...
       '$\lambda_p=2$ (Upper Bound)', ...
       '$\lambda_p=6$ (Simulation)', ...
       '$\lambda_p=6$ (Upper Bound)', ...
       'Interpreter', 'latex', 'Location', 'northwest', 'FontSize', 12);

FIGNAME = 'Fig1';
PrintFigToPaper('-depsc', FIGNAME, 16, 'Times New Roman', 7, 1, 0);
% 确保绘图正确显示
hold off;
