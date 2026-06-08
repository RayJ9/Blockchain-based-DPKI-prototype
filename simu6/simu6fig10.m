% 3D Surface Plot for PKI and DPKI Availability with Filled Region
clear; clc; close all;

% Load data
data = readtable('availability_3d_surface_data.csv');

% Extract unique values
pf_values = unique(data.pf);
ts_values = unique(data.ts);

% Create meshgrid
[PF, TS] = meshgrid(pf_values, ts_values);

% Reshape data to match meshgrid dimensions
PKI_AVAIL = reshape(data.pki_availability, length(pf_values), length(ts_values))';
DPKI_LOWER = reshape(data.dpki_lower, length(pf_values), length(ts_values))';
DPKI_UPPER = reshape(data.dpki_upper, length(pf_values), length(ts_values))';

% Create figure
figure('Position', [100, 100, 1200, 800]);

% Define colors
light_blue = [0.7, 0.85, 1.0];      % 浅蓝色 for DPKI surfaces
light_orange = [1.0, 0.8, 0.6];     % 浅橙色 for PKI
dark_purple = [0.4, 0.2, 0.6];      % 深紫色 for intersection

% Plot PKI surface
h_pki = surf(PF, TS, PKI_AVAIL, 'FaceColor', light_orange, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
hold on;

% Plot DPKI Lower Bound surface (浅蓝色)
h_dpki_lower = surf(PF, TS, DPKI_LOWER, 'FaceColor', light_blue, 'FaceAlpha', 0.3, 'EdgeColor', 'none');

% Plot DPKI Upper Bound surface (浅蓝色)
h_dpki_upper = surf(PF, TS, DPKI_UPPER, 'FaceColor', light_blue, 'FaceAlpha', 0.3, 'EdgeColor', 'none');

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

% 计算DPKI上界面与PKI面的交线
% 遍历每一个ts值，找到PKI与DPKI上界最接近的点
pf_values = PF(1, :);
intersection_points = [];

% 限制pf范围在0.2-0.8之间
pf_mask = (pf_values >= 0.2) & (pf_values <= 0.8);

disp('开始计算DPKI上界面与PKI面的交线...');
disp('遍历每个ts值，找到PKI与DPKI上界最接近的点...');

% 获取所有ts值（从第一列）
ts_values = TS(:, 1);  % 所有ts值都相同，取第一列即可

% 遍历每一个ts值
for ts_idx = 1:length(ts_values)
    ts_val = ts_values(ts_idx);
    
    min_diff = inf;
    best_pf = NaN;
    best_pki = NaN;
    best_dpki_upper = NaN;
    
    % 在当前ts值下，遍历所有pf值，找到PKI与DPKI上界最接近的点
    for pf_idx = 1:size(PF, 2)
        if pf_mask(pf_idx)
            pf_val = PF(1, pf_idx);
            pki_val = PKI_AVAIL(ts_idx, pf_idx);
            dpki_upper_val = DPKI_UPPER(ts_idx, pf_idx);
            
            % 计算PKI与DPKI上界的差值绝对值
            diff_val = abs(pki_val - dpki_upper_val);
            
            % 如果这个差值更小，更新最佳点
            if diff_val < min_diff
                min_diff = diff_val;
                best_pf = pf_val;
                best_pki = pki_val;
                best_dpki_upper = dpki_upper_val;
            end
        end
    end
    
    % 如果找到了有效的最接近点，存储它
    if ~isnan(best_pf)
        % 取PKI和DPKI上界的平均值作为交点高度
        avg_height = (best_pki + best_dpki_upper) / 2;
        intersection_points = [intersection_points; best_pf, ts_val, avg_height, min_diff];
    end
end

% 按ts值排序（从小到大）
intersection_points = sortrows(intersection_points, 2);

disp(['找到交线点数: ', num2str(size(intersection_points, 1))]);
if size(intersection_points, 1) > 0
    disp('前几个交线点 [pf, ts, availability, min_diff]:');
    disp(intersection_points(1:min(5, size(intersection_points, 1)), :));
    disp(['平均最小差值: ', num2str(mean(intersection_points(:, 4)))]);
end

% 绘制DPKI上界面与PKI面的交线
if size(intersection_points, 1) > 1
    % 按ts值排序（已经排序过了）
    % 绘制交线（紫色细线，不显示点）
    plot3(intersection_points(:,1), intersection_points(:,2), intersection_points(:,3), ...
          '-', 'Color', [0.6, 0.2, 0.8], 'LineWidth', 2);
    
    disp(['DPKI上界面与PKI面的交线已绘制完成，包含 ', num2str(size(intersection_points, 1)), ' 个点。']);
elseif size(intersection_points, 1) == 1
    % 如果只有一个交点
    plot3(intersection_points(1,1), intersection_points(1,2), intersection_points(1,3), ...
          'o', 'MarkerFaceColor', [0.6, 0.2, 0.8], 'MarkerEdgeColor', [0.3, 0.1, 0.4], ...
          'MarkerSize', 8, 'LineWidth', 2);
    disp('找到单个交点并已标记。');
else
    disp('未找到DPKI上界面与PKI面的交线。');
end

% Set labels and title
h_xlabel=xlabel('Failure Probability $p_f$', 'Interpreter', 'latex');
h_ylabel=ylabel('Threshold $t_s$', 'Interpreter', 'latex');
zlabel('Availability $A$', 'Interpreter', 'latex');

% Set axis properties
grid on;
view(45, 25);
set(h_xlabel, 'Rotation', -13, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');  % x轴标签25度，调整位置离轴近一点
set(h_ylabel, 'Rotation', 15, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');   % y轴标签与y轴平行，调整位置
xlim([min(pf_values), max(pf_values)]);
ylim([min(ts_values), max(ts_values)]);
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