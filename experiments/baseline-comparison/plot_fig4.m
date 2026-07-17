clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig4.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);
stageColors = data.stageColors;
addpath(currentDir);

%% Prototype latency comparison.
latencyFig = figure('Color', 'w', 'Position', [80, 80, 1120, 1220]);

ax1 = axes(latencyFig, 'Position', [0.028, 0.595, 0.944, 0.310]);
plotStackedLatencyH(ax1, localCellColumn(data.intraLabels), data.intraStages, data.intraTotals(:), ...
    data.intraStdTotals(:), stageColors, 'Intra-domain authentication', false);

ax2 = axes(latencyFig, 'Position', [0.028, 0.335, 0.944, 0.225]);
plotStackedLatencyH(ax2, localCellColumn(data.crossLabels), data.crossStages, data.crossTotals(:), ...
    data.crossStdTotals(:), stageColors, 'Cross-domain authentication', false);

ax3 = axes(latencyFig, 'Position', [0.028, 0.080, 0.944, 0.220]);
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
    'FontSize', 9.2, 'FontWeight', 'normal');
lgd.NumColumns = 6;
lgd.Units = 'normalized';
lgd.Position = [0.062, 0.918, 0.876, 0.048];
if isprop(lgd, 'ItemTokenSize')
    lgd.ItemTokenSize = [16, 7];
end
set(findall(lgd, '-property', 'FontWeight'), 'FontWeight', 'normal');
set(findall(latencyFig, '-property', 'FontName'), 'FontName', 'Times New Roman');

set(0, 'CurrentFigure', latencyFig);
latencyBase = fullfile(currentDir, 'figure_latency');
PrintFigToPaper('png', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.25, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('eps', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.25, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('pdf', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.25, 0);

disp(['Saved latency figure assets to ' latencyBase]);

function plotStackedLatencyH(ax, labels, stages, totals, stdTotals, colors, panelLabel, showXLabel)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'off');
set(ax, 'LineWidth', 0.80, 'FontName', 'Times New Roman', 'FontSize', 9.8, ...
    'TickLabelInterpreter', 'none');

rowCount = numel(labels);
yStep = 2.08;
y = (1:rowCount) * yStep;
b = barh(ax, y, stages, 'stacked', 'BarWidth', 0.84);
for idx = 1:numel(b)
    b(idx).FaceColor = colors(idx, :);
    b(idx).EdgeColor = [0.32, 0.32, 0.32];
    b(idx).LineWidth = 0.40;
end

for idx = 1:rowCount
    running = 0;
    for stageIdx = 1:size(stages, 2)
        value = stages(idx, stageIdx);
        if value <= 0.05
            continue;
        end
        centerX = running + value / 2;
        if value >= 8
            text(ax, centerX, y(idx), sprintf('%.1f', value), ...
                'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
                'FontName', 'Times New Roman', 'FontSize', 10.2, ...
                'FontWeight', 'normal', 'Color', [0.08, 0.08, 0.08]);
        else
            text(ax, running + value + 1.0, y(idx), sprintf('%.1f', value), ...
                'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
                'FontName', 'Times New Roman', 'FontSize', 10.2, ...
                'FontWeight', 'normal', 'Color', [0.08, 0.08, 0.08]);
        end
        running = running + value;
    end
    text(ax, totals(idx) + 3.2, y(idx), sprintf('%.1f', totals(idx)), ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 10.2, ...
        'FontWeight', 'bold', 'Color', [0.10, 0.10, 0.10], ...
        'Clipping', 'off', 'Interpreter', 'none');
    text(ax, 344.2, y(idx), normalizeLatencyLabel(labels{idx}), ...
        'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 10.2, ...
        'FontWeight', 'bold', 'Color', [0.10, 0.10, 0.10], ...
        'Clipping', 'on', 'Interpreter', 'none');
end

set(ax, 'YTick', [], 'YDir', 'reverse');
if showXLabel
    xlabel(ax, 'Latency (ms)', 'Interpreter', 'none', 'FontName', 'Times New Roman', ...
        'FontSize', 10.5, 'FontWeight', 'bold');
else
    set(ax, 'XTickLabel', []);
end
xlim(ax, [0, 350]);
xticks(ax, 0:50:300);
ylim(ax, [0.65, rowCount * yStep + 0.98]);
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 11.2, ...
    'FontWeight', 'bold', 'Interpreter', 'none');
end

function labelOut = normalizeLatencyLabel(labelIn)
labelOut = strrep(labelIn, 'our proposed', 'Our proposed');
labelOut = strrep(labelOut, 'full-contract', 'Full contract');
labelOut = strrep(labelOut, 'full contract', 'Full contract');
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
