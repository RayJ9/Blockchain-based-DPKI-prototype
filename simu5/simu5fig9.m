% MATLAB脚本：绘制'Nodes Not Responding'场景的3D可用性表面和交线
% 基于simu5_ava_p场景的计算形式

clear; clc; close all;

% 加载数据 - 先运行Python脚本转换npz文件为mat格式
disp('加载Nodes Not Responding场景数据...');
system('python -c "import numpy as np; import scipy.io; data=np.load(''surface_data_matrices_responding.npz''); scipy.io.savemat(''surface_data_matrices_responding.mat'', data)"');
data = load('surface_data_matrices_responding.mat');

% 提取数据
PF = data.PF;
TS = data.TS;
PKI_AVAIL = data.PKI_AVAIL;
DPKI_LOWER = data.DPKI_LOWER;
DPKI_UPPER = data.DPKI_UPPER;
pf_values = data.pf_values;
ts_values = data.ts_values;

disp(['数据维度: ', num2str(size(PF))]);
disp(['pf范围: [', num2str(min(pf_values)), ', ', num2str(max(pf_values)), ']']);
disp(['ts范围: [', num2str(min(ts_values)), ', ', num2str(max(ts_values)), ']']);

% 创建3D图形
figure('Position', [100, 100, 1200, 800]);

% 绘制PKI表面（半透明橙色）
h_pki = surf(PF, TS, PKI_AVAIL, 'FaceColor', [1.0, 0.8, 0.6], 'FaceAlpha', 0.3, 'EdgeColor', 'none');
hold on;

% 绘制DPKI下界面（浅蓝色）
h_dpki_lower = surf(PF, TS, DPKI_LOWER, 'FaceColor', [0.7, 0.85, 1.0], 'FaceAlpha', 0.3, 'EdgeColor', 'none');

% 绘制DPKI上界面（浅蓝色）
h_dpki_upper = surf(PF, TS, DPKI_UPPER, 'FaceColor', [0.7, 0.85, 1.0], 'FaceAlpha', 0.3, 'EdgeColor', 'none');

% 在DPKI上下界之间只在ts边界处添加连接面
% 获取ts的最大和最小值索引
ts_min_idx = find(TS(:,1) == min(ts_values));
ts_max_idx = find(TS(:,1) == max(ts_values));

% 在ts最小值处创建连接面
pf_line = PF(ts_min_idx(1), :);
ts_min_val = TS(ts_min_idx(1), :);
dpki_lower_min = DPKI_LOWER(ts_min_idx(1), :);
dpki_upper_min = DPKI_UPPER(ts_min_idx(1), :);

% 创建ts最小值处的连接面（深蓝色，不透明）
for i = 1:length(pf_line)-1
    patch([pf_line(i), pf_line(i+1), pf_line(i+1), pf_line(i)], ...
          [ts_min_val(i), ts_min_val(i+1), ts_min_val(i+1), ts_min_val(i)], ...
          [dpki_lower_min(i), dpki_lower_min(i+1), dpki_upper_min(i+1), dpki_upper_min(i)], ...
          [0.2, 0.4, 0.8], 'FaceAlpha', 1.0, 'EdgeColor', 'none');
end

% 在ts最大值处创建连接面
pf_line = PF(ts_max_idx(1), :);
ts_max_val = TS(ts_max_idx(1), :);
dpki_lower_max = DPKI_LOWER(ts_max_idx(1), :);
dpki_upper_max = DPKI_UPPER(ts_max_idx(1), :);

% 创建ts最大值处的连接面（深蓝色，不透明）
for i = 1:length(pf_line)-1
    patch([pf_line(i), pf_line(i+1), pf_line(i+1), pf_line(i)], ...
          [ts_max_val(i), ts_max_val(i+1), ts_max_val(i+1), ts_max_val(i)], ...
          [dpki_lower_max(i), dpki_lower_max(i+1), dpki_upper_max(i+1), dpki_upper_max(i)], ...
          [0.2, 0.4, 0.8], 'FaceAlpha', 1.0, 'EdgeColor', 'none');
end

% 在pf边界处创建连接面（pf=0和pf=1）
% 获取pf的最大和最小值索引
pf_min_idx = 1;  % pf最小值的列索引
pf_max_idx = size(PF, 2);  % pf最大值的列索引

% 在pf最小值处创建连接面（pf=0）
ts_line = TS(:, pf_min_idx);
pf_min_val = PF(:, pf_min_idx);
dpki_lower_pf_min = DPKI_LOWER(:, pf_min_idx);
dpki_upper_pf_min = DPKI_UPPER(:, pf_min_idx);

% 创建pf最小值处的连接面（深蓝色，不透明）
for i = 1:length(ts_line)-1
    patch([pf_min_val(i), pf_min_val(i+1), pf_min_val(i+1), pf_min_val(i)], ...
          [ts_line(i), ts_line(i+1), ts_line(i+1), ts_line(i)], ...
          [dpki_lower_pf_min(i), dpki_lower_pf_min(i+1), dpki_upper_pf_min(i+1), dpki_upper_pf_min(i)], ...
          [0.2, 0.4, 0.8], 'FaceAlpha', 1.0, 'EdgeColor', 'none');
end

% 在pf最大值处创建连接面（pf=1）
ts_line = TS(:, pf_max_idx);
pf_max_val = PF(:, pf_max_idx);
dpki_lower_pf_max = DPKI_LOWER(:, pf_max_idx);
dpki_upper_pf_max = DPKI_UPPER(:, pf_max_idx);

% 创建pf最大值处的连接面（深蓝色，不透明）
for i = 1:length(ts_line)-1
    patch([pf_max_val(i), pf_max_val(i+1), pf_max_val(i+1), pf_max_val(i)], ...
          [ts_line(i), ts_line(i+1), ts_line(i+1), ts_line(i)], ...
          [dpki_lower_pf_max(i), dpki_lower_pf_max(i+1), dpki_upper_pf_max(i+1), dpki_upper_pf_max(i)], ...
          [0.2, 0.4, 0.8], 'FaceAlpha', 1.0, 'EdgeColor', 'none');
end

% 在ts边界面上绘制PKI的深棕色边界线
% 获取PKI在ts最小值和最大值处的值
pki_min = PKI_AVAIL(ts_min_idx(1), :);
pki_max = PKI_AVAIL(ts_max_idx(1), :);

% ts最小值处的PKI边界线（深棕色，线宽减少50%）
plot3(pf_line, ts_min_val, pki_min, '-', 'Color', [0.4, 0.2, 0.1], 'LineWidth', 1);

% ts最大值处的PKI边界线（深棕色，线宽减少50%）
plot3(pf_line, ts_max_val, pki_max, '-', 'Color', [0.4, 0.2, 0.1], 'LineWidth', 1);

% 在pf=0和pf=1处添加PKI边界线
% 获取pf的最小值和最大值索引
pf_values = PF(1, :);  % 获取pf值
pf_min_idx = find(pf_values == min(pf_values));
pf_max_idx = find(pf_values == max(pf_values));

% 在pf最小值处绘制PKI边界线
ts_line_min = TS(:, pf_min_idx(1));
pki_pf_min = PKI_AVAIL(:, pf_min_idx(1));
plot3(pf_values(pf_min_idx(1)) * ones(size(ts_line_min)), ts_line_min, pki_pf_min, '-', 'Color', [0.4, 0.2, 0.1], 'LineWidth', 1);

% 在pf最大值处绘制PKI边界线
ts_line_max = TS(:, pf_max_idx(1));
pki_pf_max = PKI_AVAIL(:, pf_max_idx(1));
plot3(pf_values(pf_max_idx(1)) * ones(size(ts_line_max)), ts_line_max, pki_pf_max, '-', 'Color', [0.4, 0.2, 0.1], 'LineWidth', 1);

% 交线计算和绘制部分已移除（按用户要求）
disp('跳过交线计算和绘制，仅显示3D表面和边界线。');

% Set labels and title
xlabel('Failure Probability $p_f$', 'Interpreter', 'latex');
ylabel('Threshold $t_s$', 'Interpreter', 'latex');
zlabel('Availability $A$', 'Interpreter', 'latex');

% Set axis properties
grid on;
view(45, 30);
xlim([min(pf_values), max(pf_values)]);
ylim([0.5,1]);
zlim([0, 1]);

% Add legend
legend([h_pki, h_dpki_lower], ...
       {'PKI', 'DPKI'}, 'Location', 'best');

% Improve lighting
lighting gouraud;
camlight('headlight');

% Save figure
FIGNAME = 'Fig5s';
PrintFigToPaper('-depsc', FIGNAME, 12, 'Times New Roman', 7, 1, 0);

disp('3D plot with filled DPKI region and intersection markers generated successfully!');