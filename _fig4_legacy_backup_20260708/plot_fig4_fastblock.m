clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig4_fastblock.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);
stageColors = data.stageColors;
mechanismColors = data.mechanismColors;
addpath(currentDir);

%% Prototype latency comparison.
latencyFig = figure('Color', 'w', 'Position', [80, 80, 1120, 1220]);

ax1 = axes(latencyFig, 'Position', [0.055, 0.595, 0.910, 0.310]);
plotStackedLatencyH(ax1, localCellColumn(data.intraLabels), data.intraStages, data.intraTotals(:), ...
    data.intraStdTotals(:), stageColors, 'Intra-domain authentication', false);

ax2 = axes(latencyFig, 'Position', [0.055, 0.335, 0.910, 0.225]);
plotStackedLatencyH(ax2, localCellColumn(data.crossLabels), data.crossStages, data.crossTotals(:), ...
    data.crossStdTotals(:), stageColors, 'Cross-domain authentication', false);

ax3 = axes(latencyFig, 'Position', [0.055, 0.080, 0.910, 0.220]);
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
lgd.NumColumns = 5;
lgd.Units = 'normalized';
lgd.Position = [0.125, 0.918, 0.750, 0.048];
if isprop(lgd, 'ItemTokenSize')
    lgd.ItemTokenSize = [16, 7];
end
set(findall(lgd, '-property', 'FontWeight'), 'FontWeight', 'normal');
set(findall(latencyFig, '-property', 'FontName'), 'FontName', 'Times New Roman');

set(0, 'CurrentFigure', latencyFig);
latencyBase = fullfile(currentDir, 'figure_latency_fastblock');
PrintFigToPaper('png', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.25, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('eps', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.25, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('pdf', latencyBase, 8.2, 'Times New Roman', 8.6, 1, 0, 1, 8.25, 0);

%% Prototype overhead comparison.
overheadFig = figure('Color', 'w', 'Position', [120, 100, 1060, 760]);

costRequestLabels = {'Mgmt.', 'Intra.', 'Cross.'};
costMechanismLabels = localCellColumn(data.costMechanismLabels);

ax4 = axes(overheadFig, 'Position', [0.080, 0.585, 0.390, 0.285]);
costLegendHandles = plotGroupedCostV2(ax4, costRequestLabels, data.gasValues, mechanismColors, ...
    'On-chain gas cost', 'Gas (10^3)', '%.0f', 400);

ax5 = axes(overheadFig, 'Position', [0.575, 0.585, 0.390, 0.285]);
plotGroupedCostV2(ax5, costRequestLabels, data.recordValues, mechanismColors, ...
    'On-chain record size', 'Bytes', '%.0f', 1100);

ax6 = axes(overheadFig, 'Position', [0.095, 0.125, 0.375, 0.305]);
operationLegendHandles = plotOperationStackedH(ax6, localCellColumn(data.operationMechanismLabels), ...
    data.crossOperationCounts, data.operationColors, 'Cross-domain protocol operations');

ax7 = axes(overheadFig, 'Position', [0.575, 0.125, 0.390, 0.305]);
plotStorageGrowth(ax7, localCellColumn(data.costMechanismLabels), data.storageXRecords(:), ...
    data.storageGrowthMb, mechanismColors, 'Authentication-result storage growth');

costLegend = legend(ax4, costLegendHandles, costMechanismLabels, ...
    'Orientation', 'horizontal', 'Location', 'northoutside', 'Box', 'off', ...
    'FontName', 'Times New Roman', 'FontSize', 6.6, 'FontWeight', 'normal', ...
    'Interpreter', 'none');
costLegend.NumColumns = 4;
costLegend.Units = 'normalized';
costLegend.Position = [0.185, 0.905, 0.630, 0.040];
if isprop(costLegend, 'ItemTokenSize')
    costLegend.ItemTokenSize = [9, 5];
end
set(findall(costLegend, '-property', 'FontWeight'), 'FontWeight', 'normal');

operationLegend = legend(ax6, operationLegendHandles, localCellColumn(data.operationNames), ...
    'Orientation', 'horizontal', 'Location', 'southoutside', 'Box', 'off', ...
    'FontName', 'Times New Roman', 'FontSize', 6.2, 'FontWeight', 'normal', ...
    'Interpreter', 'none');
operationLegend.NumColumns = 3;
if isprop(operationLegend, 'ItemTokenSize')
    operationLegend.ItemTokenSize = [8, 5];
end
set(findall(operationLegend, '-property', 'FontWeight'), 'FontWeight', 'normal');
set(findall(overheadFig, '-property', 'FontName'), 'FontName', 'Times New Roman');

set(0, 'CurrentFigure', overheadFig);
overheadBase = fullfile(currentDir, 'figure_overhead_fastblock');
PrintFigToPaper('png', overheadBase, 7.2, 'Times New Roman', 5.0, 1, 0, 1, 5.20, 0);
set(0, 'CurrentFigure', overheadFig);
PrintFigToPaper('eps', overheadBase, 7.2, 'Times New Roman', 5.0, 1, 0, 1, 5.20, 0);
set(0, 'CurrentFigure', overheadFig);
PrintFigToPaper('pdf', overheadBase, 7.2, 'Times New Roman', 5.0, 1, 0, 1, 5.20, 0);

disp(['Saved fastblock latency figure assets to ' latencyBase]);
disp(['Saved fastblock overhead figure assets to ' overheadBase]);

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
    text(ax, 345.0, y(idx), labels{idx}, ...
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
xticks(ax, 0:50:350);
ylim(ax, [0.65, rowCount * yStep + 0.98]);
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 11.2, ...
    'FontWeight', 'bold', 'Interpreter', 'none');
end

function legendHandles = plotGroupedCostV2(ax, requestLabels, values, colors, panelLabel, yLabelText, valueFmt, yMax)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'off');
set(ax, 'LineWidth', 0.80, 'FontName', 'Times New Roman', 'FontSize', 7.2, ...
    'TickLabelInterpreter', 'none');

barHandles = bar(ax, values, 'grouped', 'BarWidth', 0.78);
legendHandles = gobjects(1, numel(barHandles));
for idx = 1:numel(barHandles)
    barHandles(idx).FaceColor = colors(idx, :);
    barHandles(idx).EdgeColor = [0.32, 0.32, 0.32];
    barHandles(idx).LineWidth = 0.40;
    legendHandles(idx) = barHandles(idx);
end

set(ax, 'XTick', 1:numel(requestLabels), 'XTickLabel', requestLabels);
ylabel(ax, yLabelText, 'Interpreter', 'none', 'FontName', 'Times New Roman', ...
    'FontSize', 7.6, 'FontWeight', 'bold');
ylim(ax, [0, yMax]);
xlim(ax, [0.45, numel(requestLabels) + 0.55]);
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 8.6, ...
    'FontWeight', 'bold', 'Interpreter', 'none');
end

function legendHandles = plotOperationStackedH(ax, mechanismLabels, counts, colors, panelLabel)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'off');
set(ax, 'LineWidth', 0.80, 'FontName', 'Times New Roman', 'FontSize', 7.2, ...
    'TickLabelInterpreter', 'none');

y = 1:numel(mechanismLabels);
barHandles = barh(ax, y, counts, 'stacked', 'BarWidth', 0.64);
legendHandles = gobjects(1, numel(barHandles));
for idx = 1:numel(barHandles)
    barHandles(idx).FaceColor = colors(idx, :);
    barHandles(idx).EdgeColor = [0.32, 0.32, 0.32];
    barHandles(idx).LineWidth = 0.40;
    legendHandles(idx) = barHandles(idx);
end

for rowIdx = 1:size(counts, 1)
    running = 0;
    for colIdx = 1:size(counts, 2)
        value = counts(rowIdx, colIdx);
        if value <= 0
            continue;
        end
        text(ax, running + value / 2, y(rowIdx), sprintf('%.0f', value), ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
            'FontName', 'Times New Roman', 'FontSize', 7.0, 'Color', [0.10, 0.10, 0.10]);
        running = running + value;
    end
end

set(ax, 'YTick', y, 'YTickLabel', mechanismLabels, 'YDir', 'reverse');
xlabel(ax, 'Operation count', 'Interpreter', 'none', 'FontName', 'Times New Roman', ...
    'FontSize', 7.6, 'FontWeight', 'bold');
xlim(ax, [0, max(sum(counts, 2)) + 1.0]);
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 8.6, ...
    'FontWeight', 'bold', 'Interpreter', 'none');
end

function plotStorageGrowth(ax, mechanismLabels, xRecords, storageMb, colors, panelLabel)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'on');
set(ax, 'LineWidth', 0.80, 'FontName', 'Times New Roman', 'FontSize', 7.2, ...
    'TickLabelInterpreter', 'none', 'GridLineStyle', '--', 'GridAlpha', 0.35);

for idx = 1:size(storageMb, 2)
    if max(storageMb(:, idx)) <= 0
        plot(ax, xRecords / 1000.0, storageMb(:, idx), ':', 'Color', colors(idx, :), ...
            'LineWidth', 1.2);
    else
        plot(ax, xRecords / 1000.0, storageMb(:, idx), '-o', 'Color', colors(idx, :), ...
            'LineWidth', 1.4, 'MarkerSize', 3.4, 'MarkerFaceColor', 'w');
    end
end

xlabel(ax, 'Authentication records (10^3)', 'Interpreter', 'none', ...
    'FontName', 'Times New Roman', 'FontSize', 7.6, 'FontWeight', 'bold');
ylabel(ax, 'Storage (MB)', 'Interpreter', 'none', 'FontName', 'Times New Roman', ...
    'FontSize', 7.6, 'FontWeight', 'bold');
ylim(ax, [0, max(storageMb(:)) * 1.12 + 0.1]);
xlim(ax, [min(xRecords), max(xRecords)] / 1000.0);
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 8.6, ...
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
