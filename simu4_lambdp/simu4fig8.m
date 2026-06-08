
clear; clc;

% === 读取宽表 ===
fname = 'simulation_results_by_M.csv';   % 表格文件名
T = readtable(fname);

% 兼容索引列名（应为 'M'）
if ~ismember('M', T.Properties.VariableNames)
    error('未在表格中找到列名 M，请检查文件：%s', fname);
end

M = T.M;  % 横轴

% 可用列检查
has_dpki_upper = ismember('DPKI_upper_theory', T.Properties.VariableNames);
has_dpki_lower = ismember('DPKI_lower_theory', T.Properties.VariableNames);
has_dpki_sim   = ismember('DPKI_sim',           T.Properties.VariableNames);
has_pki_theory = ismember('PKI_theory',         T.Properties.VariableNames);
has_pki_sim    = ismember('PKI_sim',            T.Properties.VariableNames);

% 取数据并转为 double
getcol = @(name) double(T{:, name});

% === 统一配色 ===
deep_green  = [0,     0.5,   0   ];
deep_orange = [1.0,   0.4,   0   ];
deep_blue   = [0.0,   0.4470,0.7410];
red         = [0.9,   0,     0   ];

% === 统一风格参数 ===
LINE_W   = 1.5;
MARK_SZ  = 5;

% === 开始绘图 ===
figure('Color','w'); hold on;

% ——显式句柄构造图例——
handles = []; labels = {};

% DPKI upper
if has_dpki_upper
    y = getcol('DPKI_upper_theory');
    h_upper = plot(M, y, '--', 'LineWidth', LINE_W, 'Color', deep_green);
    handles(end+1) = h_upper; labels{end+1} = 'DPKI Upper Bound';
end

% DPKI lower
if has_dpki_lower
    y = getcol('DPKI_lower_theory');
    h_lower = plot(M, y, '--', 'LineWidth', LINE_W, 'Color', deep_blue);
    handles(end+1) = h_lower; labels{end+1} = 'DPKI Lower Bound';
end

% ===== DPKI_sim：去空 -> 按 M 聚合 -> 阶梯拟合 + 点；图例合并为一项 =====
if has_dpki_sim
    ysim_raw = getcol('DPKI_sim');
    mask = isfinite(M) & isfinite(ysim_raw);
    Mv = M(mask);  yv = ysim_raw(mask);

    if ~isempty(yv)
        % 真实点（不进图例）
        plot(Mv, yv, 'LineStyle','none', 'Marker','o', 'MarkerSize', MARK_SZ, ...
            'MarkerEdgeColor', deep_orange, 'MarkerFaceColor', deep_orange, ...
            'HandleVisibility','off');

        % 阶梯拟合线：对相同 M 取均值
        [Mu, ~, ic] = unique(Mv(:));
        ybar = accumarray(ic, yv(:), [], @mean);
        [xs, ys] = stairs(Mu, ybar);

        % 真实阶梯线（不进图例）
        plot(xs, ys, '-', 'LineWidth', LINE_W, 'Color', deep_orange, ...
            'HandleVisibility','off');

        % ——合并图例用哑元句柄（线+点）——
        h_dpki_combo = plot(NaN, NaN, '-o', 'LineWidth', LINE_W, ...
            'Color', deep_orange, 'MarkerSize', MARK_SZ, ...
            'MarkerEdgeColor', deep_orange, 'MarkerFaceColor', deep_orange);
        handles(end+1) = h_dpki_combo; labels{end+1} = 'DPKI Analytical/Experimental';
    end
end

% ===== PKI：理论线 + 比较点；图例合并为一项 =====
h_pki_theory_real = []; h_pki_sim_real = [];
if has_pki_theory
    y = getcol('PKI_theory');
    h_pki_theory_real = plot(M, y, '-', 'LineWidth', 1.5, 'Color', red, ...
        'HandleVisibility','off');   % 真实线不进图例
end
if has_pki_sim
    y = getcol('PKI_sim');
    h_pki_sim_real = plot(M, y, 'LineStyle','none', 'Marker','o', 'MarkerSize', MARK_SZ, ...
        'MarkerFaceColor', red, 'MarkerEdgeColor', red, 'Color', red, ...
        'HandleVisibility','off');   % 真实点不进图例
end
% ——合并图例用哑元句柄（线+点）——
if has_pki_theory || has_pki_sim
    h_pki_combo = plot(NaN, NaN, '-o', 'LineWidth', 1.5, ...
        'Color', red, 'MarkerSize', MARK_SZ, ...
        'MarkerFaceColor', red, 'MarkerEdgeColor', red);
    handles(end+1) = h_pki_combo; labels{end+1} = 'PKI Analytical/Experimental';
end

% 轴标签
xlabel('$M$', 'Interpreter', 'latex');
ylabel('$E[T]$', 'Interpreter', 'latex');

grid on; set(gca, 'FontSize', 10); box on;

% 图例
if ~isempty(handles)
    legend(handles, labels,'Interpreter', 'latex', 'FontSize', 10, 'Location', 'northeast');
end

hold off;

FIGNAME = 'Fig4';
PrintFigToPaper('-depsc', FIGNAME, 16, 'Times New Roman', 7, 1, 0);