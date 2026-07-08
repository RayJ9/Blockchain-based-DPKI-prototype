clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig4.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);
stageColors = data.stageColors;
mechanismColors = data.mechanismColors;

addpath(currentDir);

%% Latency comparison: one column, three request classes.
latencyFig = figure('Color', 'w', 'Position', [80, 80, 1400, 1400]);

ax1 = axes(latencyFig, 'Position', [0.065, 0.600, 0.885, 0.305]);
plotStackedLatencyH(ax1, localCellColumn(data.intraLabels), data.intraStages, data.intraTotals(:), ...
    data.intraStdTotals(:), stageColors, 'Intra-domain authentication', false);

ax2 = axes(latencyFig, 'Position', [0.065, 0.340, 0.885, 0.225]);
plotStackedLatencyH(ax2, localCellColumn(data.crossLabels), data.crossStages, data.crossTotals(:), ...
    data.crossStdTotals(:), stageColors, 'Cross-domain authentication', false);

ax3 = axes(latencyFig, 'Position', [0.065, 0.080, 0.885, 0.225]);
plotStackedLatencyH(ax3, localCellColumn(data.mgmtLabels), data.mgmtStages, data.mgmtTotals(:), ...
    data.mgmtStdTotals(:), stageColors, 'Management', true);

legendHandles = gobjects(1, size(stageColors, 1));
legendLabels = localCellColumn(data.stageNames);
for idx = 1:size(stageColors, 1)
    legendHandles(idx) = patch(ax1, NaN, NaN, stageColors(idx, :), ...
        'EdgeColor', [0.28, 0.28, 0.28], 'LineWidth', 0.45);
end
lgd = legend(ax1, legendHandles, legendLabels, 'Orientation', 'horizontal', ...
    'Location', 'northoutside', 'Box', 'off', 'FontName', 'Times New Roman', ...
    'FontSize', 8.6, 'FontWeight', 'normal');
lgd.NumColumns = numel(legendLabels);
lgd.Units = 'normalized';
lgd.Position = [0.205, 0.938, 0.59, 0.040];
lgd.FontWeight = 'normal';
set(findall(lgd, '-property', 'FontWeight'), 'FontWeight', 'normal');
set(findall(latencyFig, '-property', 'FontName'), 'FontName', 'Times New Roman');

set(0, 'CurrentFigure', latencyFig);
latencyBase = fullfile(currentDir, 'figure_latency');
PrintFigToPaper('png', latencyBase, 9.2, 'Times New Roman', 8.6, 1, 0, 1, 8.6, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('eps', latencyBase, 9.2, 'Times New Roman', 8.6, 1, 0, 1, 8.6, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('pdf', latencyBase, 9.2, 'Times New Roman', 8.6, 1, 0, 1, 8.6, 0);

disp(['Saved latency figure assets to ' latencyBase]);

function plotStackedLatencyH(ax, labels, stages, totals, stdTotals, colors, panelLabel, showXLabel)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'off');
set(ax, 'LineWidth', 0.85, 'FontName', 'Times New Roman', 'FontSize', 9.2, ...
    'TickLabelInterpreter', 'none');

rowCount = numel(labels);
yStep = 2.05;
y = (1:rowCount) * yStep;
b = barh(ax, y, stages, 'stacked', 'BarWidth', 0.72);
for idx = 1:numel(b)
    b(idx).FaceColor = colors(idx, :);
    b(idx).EdgeColor = [0.28, 0.28, 0.28];
    b(idx).LineWidth = 0.45;
end

for idx = 1:rowCount
    running = 0;
    for stageIdx = 1:size(stages, 2)
        value = stages(idx, stageIdx);
        if value <= 0.05
            continue;
        end
        centerX = running + value / 2;
        if value >= 10
            text(ax, centerX, y(idx), sprintf('%.1f', value), ...
                'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
                'FontName', 'Times New Roman', 'FontSize', 11.2, ...
                'FontWeight', 'normal', 'Color', [0.15, 0.15, 0.15]);
        else
            text(ax, running + value + 1.2, y(idx), sprintf('%.1f', value), ...
                'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
                'FontName', 'Times New Roman', 'FontSize', 10.6, ...
                'FontWeight', 'normal', 'Color', [0.15, 0.15, 0.15]);
        end
        running = running + value;
    end
    text(ax, totals(idx) + 3.0, y(idx), sprintf('%.1f \\pm %.1f', totals(idx), stdTotals(idx)), ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 11.2, ...
        'FontWeight', 'normal', 'Color', [0.12, 0.12, 0.12], ...
        'Clipping', 'on', 'Interpreter', 'tex');
    text(ax, totals(idx) + 88.0, y(idx), labels{idx}, ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 11.2, ...
        'FontWeight', 'bold', 'Color', [0.12, 0.12, 0.12], ...
        'Clipping', 'off', 'Interpreter', 'none');
end

set(ax, 'YTick', [], 'YDir', 'reverse');
if showXLabel
    xlabel(ax, 'Latency (ms)', 'Interpreter', 'none', 'FontName', 'Times New Roman', ...
        'FontSize', 10.0, 'FontWeight', 'bold');
else
    set(ax, 'XTickLabel', []);
end
xlim(ax, [0, 650]);
xticks(ax, 0:100:600);
ylim(ax, [0.65, rowCount * yStep + 0.98]);
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 10.8, ...
    'FontWeight', 'bold', 'Interpreter', 'none');
end

function out = localCellColumn(raw)
if iscell(raw)
    out = cell(numel(raw), 1);
    for idx = 1:numel(raw)
        out{idx} = char(string(raw{idx}));
    end
else
    out = cellstr(string(raw));
end
out = out(:);
end
