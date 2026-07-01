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
latencyFig = figure('Color', 'w', 'Position', [80, 80, 1160, 1180]);
latencyLayout = tiledlayout(latencyFig, 3, 1, 'Padding', 'compact', 'TileSpacing', 'compact');

ax1 = nexttile(latencyLayout, 1);
plotStackedLatencyH(ax1, localCellColumn(data.mgmtLabels), data.mgmtStages, data.mgmtTotals(:), stageColors, '(a) Management');

ax2 = nexttile(latencyLayout, 2);
plotStackedLatencyH(ax2, localCellColumn(data.intraLabels), data.intraStages, data.intraTotals(:), stageColors, '(b) Intra-domain authentication');

ax3 = nexttile(latencyLayout, 3);
plotStackedLatencyH(ax3, localCellColumn(data.crossLabels), data.crossStages, data.crossTotals(:), stageColors, '(c) Cross-domain authentication');

legendHandles = gobjects(1, size(stageColors, 1));
legendLabels = {'Issue/update', 'Status', 'Cert. verify', 'Contract'};
for idx = 1:size(stageColors, 1)
    legendHandles(idx) = patch(ax1, NaN, NaN, stageColors(idx, :), ...
        'EdgeColor', [0.28, 0.28, 0.28], 'LineWidth', 0.45);
end
lgd = legend(ax1, legendHandles, legendLabels, 'Orientation', 'horizontal', ...
    'Location', 'northoutside', 'Box', 'off', 'FontSize', 7.2);
lgd.NumColumns = 4;

set(0, 'CurrentFigure', latencyFig);
latencyBase = fullfile(currentDir, 'figure_latency');
PrintFigToPaper('png', latencyBase, 8.8, 'Times New Roman', 7.4, 1, 0, 1, 5.55, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('eps', latencyBase, 8.8, 'Times New Roman', 7.4, 1, 0, 1, 5.55, 0);
set(0, 'CurrentFigure', latencyFig);
PrintFigToPaper('pdf', latencyBase, 8.8, 'Times New Roman', 7.4, 1, 0, 1, 5.55, 0);

%% On-chain and complexity overheads.
overheadFig = figure('Color', 'w', 'Position', [120, 120, 1540, 640]);
overheadLayout = tiledlayout(overheadFig, 1, 3, 'Padding', 'compact', 'TileSpacing', 'compact');

ax4 = nexttile(overheadLayout, 1);
plotCostH(ax4, localCellColumn(data.costRequestLabels), localCellColumn(data.costMechanismLabels), ...
    data.gasValues, mechanismColors, '(a) Gas overhead', 'Gas (10$^3$)', '%.0f');

ax5 = nexttile(overheadLayout, 2);
plotCostH(ax5, localCellColumn(data.costRequestLabels), localCellColumn(data.costMechanismLabels), ...
    data.storageValues, mechanismColors, '(b) State-write overhead', 'State write (B)', '%.0f');

ax6 = nexttile(overheadLayout, 3);
plotCostH(ax6, localCellColumn(data.complexityRequestLabels), localCellColumn(data.complexityMechanismLabels), ...
    data.complexityValues, data.statusColors, '(c) Status-validation complexity', 'Evidence count', '%.0f');

set(0, 'CurrentFigure', overheadFig);
overheadBase = fullfile(currentDir, 'figure_overhead');
PrintFigToPaper('png', overheadBase, 8.8, 'Times New Roman', 7.4, 1, 0, 1, 3.05, 0);
set(0, 'CurrentFigure', overheadFig);
PrintFigToPaper('eps', overheadBase, 8.8, 'Times New Roman', 7.4, 1, 0, 1, 3.05, 0);
set(0, 'CurrentFigure', overheadFig);
PrintFigToPaper('pdf', overheadBase, 8.8, 'Times New Roman', 7.4, 1, 0, 1, 3.05, 0);

disp(['Saved latency figure assets to ' latencyBase]);
disp(['Saved overhead figure assets to ' overheadBase]);

function plotStackedLatencyH(ax, labels, stages, totals, colors, panelLabel)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'on');
set(ax, 'LineWidth', 1.0, 'FontSize', 7.6, 'TickLabelInterpreter', 'none');

b = barh(ax, stages, 'stacked', 'BarWidth', 0.54);
for idx = 1:numel(b)
    b(idx).FaceColor = colors(idx, :);
    b(idx).EdgeColor = [0.28, 0.28, 0.28];
    b(idx).LineWidth = 0.45;
end

y = 1:numel(labels);
maxTotal = max(totals);
for idx = 1:numel(labels)
    text(ax, totals(idx) + maxTotal * 0.018, y(idx), sprintf('%.1f', totals(idx)), ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 7.0, 'Color', [0.20, 0.20, 0.20]);
end

set(ax, 'YTick', y, 'YTickLabel', labels, 'YDir', 'reverse');
xlabel(ax, 'Latency (ms)', 'Interpreter', 'latex', 'FontSize', 8.8, 'FontWeight', 'bold');
xlim(ax, [0, maxTotal * 1.17]);
ylim(ax, [0.20, numel(labels) + 0.50]);
ax.GridAlpha = 0.18;
title(ax, panelLabel, 'FontName', 'Times New Roman', 'FontSize', 9.2, ...
    'FontWeight', 'bold', 'Interpreter', 'none');
end

function plotCostH(ax, requestLabels, mechanismLabels, values, colors, panelLabel, xLabelText, valueFmt)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'on');
set(ax, 'LineWidth', 1.0, 'FontSize', 7.4, 'TickLabelInterpreter', 'none');

flatLabels = {};
flatValues = [];
flatColors = [];
for r = 1:size(values, 1)
    for c = 1:size(values, 2)
        flatLabels{end + 1, 1} = sprintf('%s-%s', shortName(mechanismLabels{c}), shortName(requestLabels{r})); %#ok<AGROW>
        flatValues(end + 1, 1) = values(r, c); %#ok<AGROW>
        flatColors(end + 1, :) = colors(c, :); %#ok<AGROW>
    end
end

y = 1:numel(flatValues);
bars = barh(ax, y, flatValues, 'BarWidth', 0.58);
bars.FaceColor = 'flat';
bars.CData = flatColors;
bars.EdgeColor = [0.28, 0.28, 0.28];
bars.LineWidth = 0.45;

maxVal = max(flatValues(:));
if maxVal <= 0
    maxVal = 1;
end
for idx = 1:numel(flatValues)
    if flatValues(idx) > 0
        text(ax, flatValues(idx) + maxVal * 0.018, y(idx), sprintf(valueFmt, flatValues(idx)), ...
            'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
            'FontName', 'Times New Roman', 'FontSize', 6.7, 'Color', [0.20, 0.20, 0.20]);
    end
end

set(ax, 'YTick', y, 'YTickLabel', flatLabels, 'YDir', 'reverse');
xlabel(ax, xLabelText, 'Interpreter', 'latex', 'FontSize', 8.6, 'FontWeight', 'bold');
xlim(ax, [0, maxVal * 1.22]);
ylim(ax, [0.05, numel(flatValues) + 0.55]);
ax.GridAlpha = 0.18;
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

function out = shortName(raw)
name = char(string(raw));
switch name
    case 'DPKI-On'
        out = 'DPKI';
    case 'OCSP-On'
        out = 'OCSP';
    case 'Threshold'
        out = 'Thr';
    case 'Contract'
        out = 'Cont';
    case 'PKI-OCSP'
        out = 'PKI';
    case 'Mgmt'
        out = 'M';
    case 'Intra'
        out = 'I';
    case 'Cross'
        out = 'C';
    otherwise
        out = name;
end
end
