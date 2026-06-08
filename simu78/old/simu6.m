% --- 1. 初始化工作区 ---
clear;
clc;
close all;

% --- 2. 从 CSV 文件加载数据 ---
% 确保 'theoretical_availability_malicious_vs_pf_unified' 在同一目录下
try
    data = readtable('theoretical_availability_malicious_vs_pf_unified.csv');
catch ME
    error('无法读取 CSV 文件。请确保 theoretical_availability_malicious_vs_pf.csv 文件存在于当前目录。');
end

% --- 3. 准备绘图 ---
figure('Position', [100, 100, 900, 600]);
hold on;

% 从Python脚本中获取或在此处定义关键参数，用于绘图
CONSENSUS_THRESHOLD_P_TH = 0.5; % 必须与生成数据的Python脚本中的值一致

% 获取所有唯一的 m 值
m_values = unique(data.m);
num_m_values = length(m_values);

pki_colors = [
    0.8500, 0.3250, 0.0980;     % 红
    0.9290, 0.6940, 0.1250;     % 橙
    0.717, 0.275, 0.188;       % 深红
];
dpki_colors = [
    0, 0.4470, 0.7410;      % 蓝
    0.3010, 0.7450, 0.9330; % 淡蓝
    0.07, 0.62, 0.17;    % 绿
];


% --- 4. 循环遍历每个 m 值并绘图 ---
for i = 1:num_m_values
    m_val = m_values(i);
    m_data = data(data.m == m_val, :);
    
    % 提取 x 和 y 轴数据
    pf = m_data.pf;
    pki_avail = m_data.PKI;
    dpki_lower = m_data.DPKI_Mal_Lower;
    dpki_upper = m_data.DPKI_Mal_Upper;
    
    % 绘制 PKI 曲线
    plot(pf, pki_avail, ...
        'Color', pki_colors(i,:), ...
        'LineWidth', 2.5, ...
        'LineStyle', '-', ...
        'DisplayName', sprintf('PKI (m=%d)', m_val));
        
    % 绘制 DPKI 上下界曲线
    plot(pf, dpki_upper, ...
        'Color', dpki_colors(i,:), ...
        'LineWidth', 2.0, ...
        'LineStyle', '--', ...
        'HandleVisibility', 'off');

    plot(pf, dpki_lower, ...
        'Color', dpki_colors(i,:), ...
        'LineWidth', 2.0, ...
        'LineStyle', ':', ...
        'HandleVisibility', 'off');
        
    % 填充 DPKI 的理论范围
    fill_x = [pf; flipud(pf)];
    fill_y = [dpki_lower; flipud(dpki_upper)];
    
    fill(fill_x, fill_y, dpki_colors(i,:), ...
        'FaceAlpha', 0.15, ...
        'EdgeColor', 'none', ...
        'DisplayName', sprintf('DPKI Range (m=%d)', m_val));
end

% --- 5. 格式化图表 ---
% 添加共识阈值垂直线
xline(CONSENSUS_THRESHOLD_P_TH, '-.', 'Color', [0.2 0.2 0.2], 'LineWidth', 2, ...
    'DisplayName', sprintf('Consensus Threshold', CONSENSUS_THRESHOLD_P_TH), ...
    'Label', 'Consensus Failure', 'LabelOrientation', 'horizontal', 'LabelVerticalAlignment', 'bottom');

% 添加标题和坐标轴标签
title('Availability vs. Malicious Node Probability', 'FontSize', 16);
xlabel('Malicious Node Probability ($p_f$)', 'Interpreter', 'latex', 'FontSize', 14);
ylabel('System Availability $A(p_f)$', 'Interpreter', 'latex', 'FontSize', 14);

% 设置坐标轴范围和刻度
xlim([0, 1]);
ylim([0, 1.05]);
xticks(0:0.1:1);
yticks(0:0.1:1);

% --- MODIFIED: 修正 legend 和 grid 的代码 ---

% 创建图例并获取其句柄
lgd = legend('Location', 'southwest', 'FontSize', 12);

lgd.Title.FontSize = 11;

% 确保网格可见
grid on;
box on;
ax = gca;
ax.FontSize = 12;
ax.GridAlpha = 1; % 设置网格为完全不透明
ax.GridLineStyle = ':';
ax.Layer = 'top';

hold off;

FIGNAME = 'Fig6';
PrintFigToPaper('-depsc', FIGNAME, 16, 'Times New Roman', 7, 1, 0);