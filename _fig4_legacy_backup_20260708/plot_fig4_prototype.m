clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig4_prototype.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);
stageColors = data.stageColors;
mechanismColors = data.mechanismColors;
addpath(currentDir);

%% Prototype latency comparison.
latencyFig = figure('Color', 'w', 'Position', [80, 80, 1180, 1220]);

ax1 = axes(latencyFig, 'Position', [0.065, 0.595, 0.885, 0.310]);
plotStackedLatencyH(ax1, localCellColumn(data.intraLabels), data.intraStages, data.intraTotals(:), ...
    data.intraStdTotals(:), stageColors, 'Intra-domain authentication', false);

ax2 = axes(latencyFig, 'Position', [0.065, 0.335, 0.885, 0.225]);
plotStackedLatencyH(ax2, localCellColumn(data.crossLabels), data.crossStages, data.crossTotals(:), ...
    data.crossStdTotals(:), stageColors, 'Cross-domain authentication', false);

ax3 = axes(latencyFig, 'Position', [0.065, 0.080, 0.885, 0.220]);
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
    'FontSize', 8.2, 'FontWeight', 'normal');
lgd.NumColumns = 4;
lgd.Units = 'normalized';
lgd.Position = [0.145, 0.930, 0.710, 0.052];
set(findall(lgd, '-property', 'FontWeight'), 'FontWeight', 'normal');
set(findall(latencyFig, '-property', 'FontName'), 'FontName', 'Times New Roman');

set(0, 'CurrentFigure', latencyFig);
latencyBase = fullfile(currentDir, 'figure_latency_prototype');
PrintFigToPaper('png', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.6, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('eps', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.6, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('pdf', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.6, 0);

%% Prototype overhead comparison.
overheadFig = figure('Color', 'w', 'Position', [120, 100, 600, 900]);

ax4 = axes(overheadFig, 'Position', [0.135, 0.505, 0.835, 0.325]);
costLegendHandles = plotGroupedCostV(ax4, localCellColumn(data.costRequestLabels), localCellColumn(data.costMechanismLabels), ...
    data.gasValues, mechanismColors, 'Gas overhead', 'Gas (10^3)', '%.0f', false);

ax5 = axes(overheadFig, 'Position', [0.135, 0.075, 0.835, 0.325]);
plotGroupedCostV(ax5, localCellColumn(data.costRequestLabels), localCellColumn(data.costMechanismLabels), ...
    data.recordValues, mechanismColors, 'On-chain record overhead', 'Record (Byte)', '%.0f', true);

costLegendLabels = localCellColumn(data.costMechanismLabels);
costLegend = legend(ax4, costLegendHandles, costLegendLabels, ...
    'Orientation', 'horizontal', 'Location', 'northoutside', 'Box', 'off', ...
    'FontName', 'Times New Roman', 'FontSize', 6.0, 'FontWeight', 'normal', ...
    'Interpreter', 'none');
costLegend.NumColumns = 4;
costLegend.Units = 'normalized';
costLegend.Position = [0.070, 0.870, 0.860, 0.050];
if isprop(costLegend, 'ItemTokenSize')
    costLegend.ItemTokenSize = [7, 5];
end
set(findall(costLegend, '-property', 'FontWeight'), 'FontWeight', 'normal');
set(findall(overheadFig, '-property', 'FontName'), 'FontName', 'Times New Roman');

set(0, 'CurrentFigure', overheadFig);
overheadBase = fullfile(currentDir, 'figure_overhead_prototype');
PrintFigToPaper('png', overheadBase, 6.0, 'Times New Roman', 5.0, 1, 0, 1, 4.7, 0);
set(0, 'CurrentFigure', overheadFig);
PrintFigToPaper('eps', overheadBase, 6.0, 'Times New Roman', 5.0, 1, 0, 1, 4.7, 0);
set(0, 'CurrentFigure', overheadFig);
PrintFigToPaper('pdf', overheadBase, 6.0, 'Times New Roman', 5.0, 1, 0, 1, 4.7, 0);

disp(['Saved prototype latency figure assets to ' latencyBase]);
disp(['Saved prototype overhead figure assets to ' overheadBase]);

function plotStackedLatencyH(ax, labels, stages, totals, stdTotals, colors, panelLabel, showXLabel)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'off');
set(ax, 'LineWidth', 0.85, 'FontName', 'Times New Roman', 'FontSize', 9.2, ...
    'TickLabelInterpreter', 'none');

rowCount = numel(labels);
yStep = 2.08;
y = (1:rowCount) * yStep;
b = barh(ax, y, stages, 'stacked', 'BarWidth', 0.74);
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
        if value >= 8
            text(ax, centerX, y(idx), sprintf('%.1f', value), ...
                'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
                'FontName', 'Times New Roman', 'FontSize', 10.2, ...
                'FontWeight', 'normal', 'Color', [0.15, 0.15, 0.15]);
        else
            text(ax, running + value + 1.0, y(idx), sprintf('%.1f', value), ...
                'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
                'FontName', 'Times New Roman', 'FontSize', 9.6, ...
                'FontWeight', 'normal', 'Color', [0.15, 0.15, 0.15]);
        end
        running = running + value;
    end
    text(ax, totals(idx) + 2.5, y(idx), sprintf('%.1f \\pm %.1f', totals(idx), stdTotals(idx)), ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 10.2, ...
        'FontWeight', 'normal', 'Color', [0.12, 0.12, 0.12], ...
        'Clipping', 'off', 'Interpreter', 'tex');
    text(ax, 515.0, y(idx), labels{idx}, ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 10.2, ...
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

function legendHandles = plotGroupedCostV(ax, requestLabels, mechanismLabels, values, colors, panelLabel, yLabelText, valueFmt, showXLabels)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'off');
set(ax, 'LineWidth', 0.85, 'FontName', 'Times New Roman', 'FontSize', 7.4, ...
    'TickLabelInterpreter', 'none');

maxVal = max(values(:));
if maxVal <= 0
    maxVal = 1;
end

numGroups = size(values, 1);
numSeries = size(values, 2);
groupCenters = 1 + (0:numGroups-1) * 0.28;
seriesOffsets = linspace(-0.070, 0.070, numSeries);
barWidth = 0.035;
legendHandles = gobjects(1, numSeries);
for c = 1:numSeries
    for r = 1:numGroups
        xPosition = groupCenters(r) + seriesOffsets(c);
        h = bar(ax, xPosition, values(r, c), barWidth, ...
            'FaceColor', colors(c, :), ...
            'EdgeColor', [0.28, 0.28, 0.28], ...
            'LineWidth', 0.45);
        if r == 1
            legendHandles(c) = h;
        else
            h.HandleVisibility = 'off';
        end
        value = values(r, c);
        if value > 0
            text(ax, xPosition, value + maxVal * 0.025, sprintf(valueFmt, value), ...
                'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', ...
                'FontName', 'Times New Roman', 'FontSize', 7.8, 'Color', [0.20, 0.20, 0.20]);
        end
    end
end

if showXLabels
    set(ax, 'XTick', groupCenters, 'XTickLabel', requestLabels);
else
    set(ax, 'XTick', groupCenters, 'XTickLabel', []);
end
ylabel(ax, yLabelText, 'Interpreter', 'none', 'FontName', 'Times New Roman', ...
    'FontSize', 8.4, 'FontWeight', 'bold');
ylim(ax, [0, maxVal * 1.18]);
xlim(ax, [groupCenters(1) + seriesOffsets(1) - 0.070, groupCenters(end) + seriesOffsets(end) + 0.070]);
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 9.0, ...
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
