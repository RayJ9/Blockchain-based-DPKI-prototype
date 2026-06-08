%% PKI vs DPKI 系统可用性 3D 切面图 - MATLAB可视化版本
% 仅负责读取CSV数据并生成3D切面图
% 使用统一的颜色方案：PKI=[0.8500, 0.3250, 0.0980], DPKI=[0, 0.4470, 0.7410]

clear; clc; close all;

%% ========================================================================
%% 读取CSV数据
%% ========================================================================

fprintf('--- 开始读取CSV数据并生成3D切面图 ---\n');

% 读取数据文件
data_file = 'availability_pf_m_slices_3d_data.csv';
if ~exist(data_file, 'file')
    error('数据文件 %s 不存在！请先运行Python代码生成数据。', data_file);
end

% 读取CSV数据
data_table = readtable(data_file);
fprintf('成功读取数据文件: %s\n', data_file);
fprintf('数据行数: %d\n', height(data_table));

% 提取数据
pf_values = data_table.pf;
m_values = data_table.m;
pki_values = data_table.PKI;
dpki_lower_values = data_table.DPKI_Lower;
dpki_upper_values = data_table.DPKI_Upper;
dpki_values = data_table.DPKI_Mean;

% 获取参数范围
unique_pf = unique(pf_values);
unique_m = unique(m_values);

fprintf('pf范围: %.1f - %.1f (%d个点)\n', min(unique_pf), max(unique_pf), length(unique_pf));
fprintf('M范围: %d - %d (%d个值)\n', min(unique_m), max(unique_m), length(unique_m));

%% ========================================================================
%% 创建3D切面图
%% ========================================================================

% 创建图形窗口
figure('Position', [100, 100, 1200, 900]);

% 定义统一颜色 - 严格按照用户要求
PKI_COLOR = [0.8500, 0.3250, 0.0980];  % 橙红色
DPKI_COLOR = [0, 0.4470, 0.7410];      % 蓝色
BACKGROUND_COLOR = [0.9, 0.9, 0.9];    % 更浅的灰色背景

% 创建3D图形
hold on;

% 为每个M值创建切片效果
for i = 1:length(unique_m)
    m = unique_m(i);
    
    % 提取当前M值的数据
    m_indices = (m_values == m);
    current_pf = pf_values(m_indices);
    current_pki = pki_values(m_indices);
    current_dpki_lower = dpki_lower_values(m_indices);
    current_dpki_upper = dpki_upper_values(m_indices);
    current_dpki = dpki_values(m_indices);
    
    % 按pf排序
    [current_pf, sort_idx] = sort(current_pf);
    current_pki = current_pki(sort_idx);
    current_dpki_lower = current_dpki_lower(sort_idx);
    current_dpki_upper = current_dpki_upper(sort_idx);
    current_dpki = current_dpki(sort_idx);
    
    % 创建切片底色平面 - 浅灰色透明底色
    % 创建一个矩形平面作为切片底色
    pf_min = min(current_pf);
    pf_max = max(current_pf);
    availability_min = 0;
    availability_max = 1;
    
    % 定义切片平面的四个角点
    slice_pf = [pf_min, pf_max, pf_max, pf_min];
    slice_m = [m, m, m, m];
    slice_availability = [availability_min, availability_min, availability_max, availability_max];
    
    % 绘制切片底色 - 已注释掉
    % fill3(slice_pf, slice_m, slice_availability, BACKGROUND_COLOR, ...
    %       'FaceAlpha', 0.1, 'EdgeColor', 'none', 'HandleVisibility', 'off');
    
    % 在同一平面上绘制PKI线条（无点标记）
    if i == 1  % 只在第一次循环时添加到图例
        plot3(current_pf, repmat(m, size(current_pf)), current_pki, ...
              'Color', PKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
              'DisplayName', 'PKI');
    else
        plot3(current_pf, repmat(m, size(current_pf)), current_pki, ...
              'Color', PKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
              'HandleVisibility', 'off');
    end
    
    % 绘制DPKI下界线条（实线，无点标记）
    if i == 1
        % 只在第一条线上添加图例，合并DPKI上下界为一个图例项
        plot3(current_pf, repmat(m, size(current_pf)), current_dpki_lower, ...
              'Color', DPKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
              'DisplayName', 'DPKI');
    else
        plot3(current_pf, repmat(m, size(current_pf)), current_dpki_lower, ...
              'Color', DPKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
              'HandleVisibility', 'off');
    end
    
    % 绘制DPKI上界线条（实线，无点标记）
    plot3(current_pf, repmat(m, size(current_pf)), current_dpki_upper, ...
          'Color', DPKI_COLOR, 'LineWidth', 1, 'LineStyle', '-', ...
          'HandleVisibility', 'off');
    
    % 在DPKI上下界之间添加平面连接
    for k = 1:length(current_pf)-1
        % 创建四边形面片连接相邻的上下界点
        x_quad = [current_pf(k), current_pf(k+1), current_pf(k+1), current_pf(k)];
        y_quad = [m, m, m, m];
        z_quad = [current_dpki_lower(k), current_dpki_lower(k+1), current_dpki_upper(k+1), current_dpki_upper(k)];
        
        % 绘制半透明的面片
        patch(x_quad, y_quad, z_quad, DPKI_COLOR, 'FaceAlpha', 0.3, ...
              'EdgeColor', 'none', 'HandleVisibility', 'off');
    end
end

%% ========================================================================
%% 添加投影效果
%% ========================================================================

% 定义投影的透明度和颜色
projection_alpha = 0.3;
projection_pki_color = [PKI_COLOR, projection_alpha];
projection_dpki_color = [DPKI_COLOR, projection_alpha];

% 投影到A-M面上 (YZ平面, pf=0)
% 首先绘制投影平面的白色底色
m_range = [min(unique_m), max(unique_m)];
a_range = [0, 1];  % A轴范围恢复为完整的0-1

% 创建投影平面的四个角点
projection_m = [m_range(1), m_range(2), m_range(2), m_range(1)];
projection_pf = [0.001, 0.001, 0.001, 0.001];  % pf=0.001平面
projection_a = [a_range(1), a_range(1), a_range(2), a_range(2)];

% 绘制白色投影平面底色
fill3(projection_pf, projection_m, projection_a, 'white', ...
      'FaceAlpha', 0.9, 'EdgeColor', 'none', 'HandleVisibility', 'off');

% 为指定的pf值绘制DPKI在A-M面上的投影
selected_pf_values = [0.2, 0.4, 0.6, 0.8];

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
    current_dpki = dpki_values(pf_indices);
    
    % 在A-M面绘制DPKI下界投影 (pf=0.001处) - 蓝色虚线
    plot3(zeros(size(current_m)) + 0.001, current_m, current_dpki_lower, ...
          'Color', DPKI_COLOR, 'LineWidth', 1.5, 'LineStyle', '--', ...
          'HandleVisibility', 'off', 'Marker', 'none');
    
    % 在A-M面绘制DPKI上界投影 (pf=0.001处) - 蓝色虚线
    plot3(zeros(size(current_m)) + 0.001, current_m, current_dpki_upper, ...
          'Color', DPKI_COLOR, 'LineWidth', 1.5, 'LineStyle', '--', ...
          'HandleVisibility', 'off', 'Marker', 'none');
    
    % 在两条投影线之间添加绿色填充 (pf=0.001处)
    % 创建填充区域的顶点
    fill_m = [current_m; flipud(current_m)];
    fill_pf = zeros(size(fill_m)) + 0.001;
    fill_z = [current_dpki_lower; flipud(current_dpki_upper)];
    
    % 绘制绿色填充区域
    fill3(fill_pf, fill_m, fill_z, 'green', 'FaceAlpha', 0.2, ...
          'EdgeColor', 'none', 'HandleVisibility', 'off');
    
    % 添加从3D点到投影点的连接线
    for j = 1:length(current_m)
        % 找到对应的3D点
        m_val = current_m(j);
        dpki_lower_val = current_dpki_lower(j);
        dpki_upper_val = current_dpki_upper(j);
        
        % 绘制从3D点到投影点的浅灰色虚线
        plot3([target_pf, 0.001], [m_val, m_val], [dpki_lower_val, dpki_lower_val], ...
              'Color', [0.7, 0.7, 0.7], 'LineWidth', 1.0, 'LineStyle', '--', ...
              'HandleVisibility', 'off');
        
        plot3([target_pf, 0.001], [m_val, m_val], [dpki_upper_val, dpki_upper_val], ...
              'Color', [0.7, 0.7, 0.7], 'LineWidth', 1.0, 'LineStyle', '--', ...
              'HandleVisibility', 'off');
    end
    
    % 添加pf标签
    % 找到M最大值位置作为标签位置
    [sorted_m, sort_idx] = sort(current_m);
    sorted_dpki = current_dpki(sort_idx);
    max_m = max(sorted_m);
    max_m_idx = find(sorted_m == max_m, 1);
    label_m = sorted_m(max_m_idx);
    label_dpki = sorted_dpki(max_m_idx);
    
    % 在投影平面上添加文本标签（放在M最大值右边）
    text(0.05, label_m + 0.5, label_dpki, sprintf('pf=%.1f', target_pf), ...
         'FontSize', 10, 'Color', 'black', 'FontName', 'Times New Roman', ...
         'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
end

% 绘制每条DPKI投影折线的包络线并填充区域
% 为每条投影折线（pf=0.2, 0.4, 0.6, 0.8）分别将奇数M和偶数M的点拟合成包络线
% 延伸到整个投影平面并根据趋势填充颜色

% 定义投影平面的范围
m_range = [4, 12];  % M轴范围
a_range = [0, 1];   % A轴范围（DPKI可用性范围）恢复为完整的0-1

% 存储所有包络线数据用于填充
all_envelopes = {};

for i = 1:length(selected_pf_values)
    target_pf = selected_pf_values(i);
    [~, closest_idx] = min(abs(unique_pf - target_pf));
    pf = unique_pf(closest_idx);
    
    % 获取当前pf值的数据
    pf_indices = (pf_values == pf);
    current_m = m_values(pf_indices);
    current_dpki = dpki_values(pf_indices);
    
    % 分离奇数M和偶数M的点
    odd_m_indices = mod(current_m, 2) == 1;  % 奇数M值 (5,7,9,11)
    even_m_indices = mod(current_m, 2) == 0; % 偶数M值 (4,6,8,10,12)
    
    % 奇数M值的点
    odd_m = current_m(odd_m_indices);
    odd_dpki = current_dpki(odd_m_indices);
    
    % 偶数M值的点
    even_m = current_m(even_m_indices);
    even_dpki = current_dpki(even_m_indices);
    
    % 处理奇数M值的包络线
    if length(odd_m) >= 2
        [sorted_odd_m, sort_idx] = sort(odd_m);
        sorted_odd_dpki = odd_dpki(sort_idx);
        
        % 使用多项式拟合（2次）
        if length(sorted_odd_m) >= 3
            p_odd = polyfit(sorted_odd_m, sorted_odd_dpki, 2);
        else
            p_odd = polyfit(sorted_odd_m, sorted_odd_dpki, 1);
        end
        
        % 延伸到整个M轴范围
        m_extended = linspace(m_range(1), m_range(2), 100);
        dpki_extended_odd = polyval(p_odd, m_extended);
        
        % 限制在A轴范围内
        dpki_extended_odd = max(a_range(1), min(a_range(2), dpki_extended_odd));
        
        % 存储包络线数据
        all_envelopes{end+1} = struct('pf', target_pf, 'type', 'odd', ...
                                     'm', m_extended, 'dpki', dpki_extended_odd);
    end
    
    % 处理偶数M值的包络线
    if length(even_m) >= 2
        [sorted_even_m, sort_idx] = sort(even_m);
        sorted_even_dpki = even_dpki(sort_idx);
        
        % 使用多项式拟合（2次）
        if length(sorted_even_m) >= 3
            p_even = polyfit(sorted_even_m, sorted_even_dpki, 2);
        else
            p_even = polyfit(sorted_even_m, sorted_even_dpki, 1);
        end
        
        % 延伸到整个M轴范围
        m_extended = linspace(m_range(1), m_range(2), 100);
        dpki_extended_even = polyval(p_even, m_extended);
        
        % 限制在A轴范围内
        dpki_extended_even = max(a_range(1), min(a_range(2), dpki_extended_even));
        
        % 存储包络线数据
        all_envelopes{end+1} = struct('pf', target_pf, 'type', 'even', ...
                                     'm', m_extended, 'dpki', dpki_extended_even);
    end
end

% 绘制填充区域和边框
for i = 1:length(selected_pf_values)
    target_pf = selected_pf_values(i);
    
    % 找到当前pf对应的奇数和偶数包络线
    odd_envelope = [];
    even_envelope = [];
    
    for j = 1:length(all_envelopes)
        if all_envelopes{j}.pf == target_pf
            if strcmp(all_envelopes{j}.type, 'odd')
                odd_envelope = all_envelopes{j};
            else
                even_envelope = all_envelopes{j};
            end
        end
    end
    
    % 如果两条包络线都存在，绘制填充区域
    if ~isempty(odd_envelope) && ~isempty(even_envelope)
        % 确定颜色和趋势
        if target_pf <= 0.4  % pf=0.2, 0.4 上升趋势，绿色
            fill_color = [0.2, 0.8, 0.2];  % 绿色
            edge_color = [0.0, 0.6, 0.0];  % 深绿色
            line_style = '--';
        else  % pf=0.6, 0.8 下降趋势，红色
            fill_color = [0.8, 0.2, 0.2];  % 红色
            edge_color = [0.6, 0.0, 0.0];  % 深红色
            line_style = '--';
        end
        
        % 确保包络线数据点数相同，并且排序正确
        m_common = linspace(m_range(1), m_range(2), 100);
        odd_dpki_interp = interp1(odd_envelope.m, odd_envelope.dpki, m_common, 'linear', 'extrap');
        even_dpki_interp = interp1(even_envelope.m, even_envelope.dpki, m_common, 'linear', 'extrap');
        
        % 限制在A轴范围内
        odd_dpki_interp = max(a_range(1), min(a_range(2), odd_dpki_interp));
        even_dpki_interp = max(a_range(1), min(a_range(2), even_dpki_interp));
        
        % 创建填充区域的顶点（确保闭合）
        m_fill = [m_common, fliplr(m_common)];
        dpki_fill = [odd_dpki_interp, fliplr(even_dpki_interp)];
        z_fill = zeros(size(m_fill));  % 在投影平面上
        
        % 绘制填充区域
        fill3(z_fill, m_fill, dpki_fill, fill_color, ...
              'FaceAlpha', 0.5, 'EdgeColor', 'none', 'HandleVisibility', 'off');
        
        % 绘制边框线
        plot3(zeros(size(m_common)), m_common, odd_dpki_interp, ...
              'Color', edge_color, 'LineWidth', 1.5, 'LineStyle', line_style, ...
              'HandleVisibility', 'off');
        
        plot3(zeros(size(m_common)), m_common, even_dpki_interp, ...
              'Color', edge_color, 'LineWidth', 1.5, 'LineStyle', line_style, ...
              'HandleVisibility', 'off');
    end
end

%% ========================================================================
%% 设置图形属性
%% ========================================================================

% 设置坐标轴
h_xlabel=xlabel('Failure Probability $p_f$', 'Interpreter', 'latex');
h_ylabel=ylabel('Service CA Number $M$', 'Interpreter', 'latex');
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
set(h_xlabel, 'Rotation', -25, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');  % x轴标签25度，调整位置离轴近一点
set(h_ylabel, 'Rotation', 25, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');   % y轴标签与y轴平行，调整位置

% 移除网格和背景
grid on;
set(gca, 'XColor', 'k', 'YColor', 'k', 'ZColor', 'k');

hold off;


% 保存图形
output_filename = 'availability_pf_m_slices_3d_matlab_unified.png';
saveas(gcf, output_filename);
fprintf('3D切面图已保存为: %s\n', output_filename);

% 显示关键统计信息
fprintf('\n=== 关键统计信息 ===\n');
fprintf('PKI最大可用性: %.4f\n', max(pki_values));
fprintf('PKI最小可用性: %.4f\n', min(pki_values));
fprintf('DPKI最大可用性: %.4f\n', max(dpki_values));
fprintf('DPKI最小可用性: %.4f\n', min(dpki_values));

% 找到最优配置
[~, best_pki_idx] = max(pki_values);
[~, best_dpki_idx] = max(dpki_values);

fprintf('\nPKI最优配置: pf=%.2f, M=%d, A=%.4f\n', ...
        pf_values(best_pki_idx), m_values(best_pki_idx), pki_values(best_pki_idx));
fprintf('DPKI最优配置: pf=%.2f, M=%d, A=%.4f\n', ...
        pf_values(best_dpki_idx), m_values(best_dpki_idx), dpki_values(best_dpki_idx));

% 显示颜色信息
fprintf('\n=== 颜色方案 ===\n');
fprintf('PKI颜色: [%.4f, %.4f, %.4f] (橙红色)\n', PKI_COLOR);
fprintf('DPKI颜色: [%.4f, %.4f, %.4f] (蓝色)\n', DPKI_COLOR);
fprintf('背景颜色: [%.1f, %.1f, %.1f] (淡灰色)\n', BACKGROUND_COLOR);
FIGNAME = 'Fig6';
PrintFigToPaper('-depsc', FIGNAME, 12, 'Times New Roman', 7, 1, 0);
fprintf('\n程序执行完成！\n');