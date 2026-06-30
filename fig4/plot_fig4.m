clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig4.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);
stageColors = data.stageColors;
mechanismColors = data.mechanismColors;

figure1 = figure('Color', 'w', 'Position', [80, 80, 1660, 1080]);
t = tiledlayout(figure1, 2, 3, 'Padding', 'compact', 'TileSpacing', 'compact');

ax1 = nexttile(t, 1);
plotStackedLatencyH(ax1, localCellColumn(data.mgmtLabels), data.mgmtStages, data.mgmtTotals(:), stageColors, '(a) Management');

ax2 = nexttile(t, 2);
plotStackedLatencyH(ax2, localCellColumn(data.intraLabels), data.intraStages, data.intraTotals(:), stageColors, '(b) Intra-domain auth.');

ax3 = nexttile(t, 3);
plotStackedLatencyH(ax3, localCellColumn(data.crossLabels), data.crossStages, data.crossTotals(:), stageColors, '(c) Cross-domain auth.');

ax4 = nexttile(t, 4);
plotCostH(ax4, localCellColumn(data.costRequestLabels), localCellColumn(data.costMechanismLabels), ...
    data.gasValues, mechanismColors, '(d) Gas overhead', 'Gas (10$^3$)', '%.0f');

ax5 = nexttile(t, 5);
plotCostH(ax5, localCellColumn(data.costRequestLabels), localCellColumn(data.costMechanismLabels), ...
    data.storageValues, mechanismColors, '(e) State-write overhead', 'State write (B)', '%.0f');

ax6 = nexttile(t, 6);
plotCostH(ax6, localCellColumn(data.statusRequestLabels), localCellColumn(data.statusMechanismLabels), ...
    data.statusValues, mechanismColors, '(f) Status-validation primitive', 'Latency (ms)', '%.1f');

outBase = fullfile(currentDir, 'figure');
addpath(currentDir);
set(0, 'CurrentFigure', figure1);
PrintFigToPaper('png', outBase, 13, 'Times New Roman', 7.4, 1, 0, 1, 5.45, 0);
set(0, 'CurrentFigure', figure1);
PrintFigToPaper('eps', outBase, 13, 'Times New Roman', 7.4, 1, 0, 1, 5.45, 0);
set(0, 'CurrentFigure', figure1);
PrintFigToPaper('pdf', outBase, 13, 'Times New Roman', 7.4, 1, 0, 1, 5.45, 0);

disp(['Saved figure assets to ' outBase]);

function plotStackedLatencyH(ax, labels, stages, totals, colors, panelLabel)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'on');
set(ax, 'LineWidth', 1.0, 'FontSize', 7.6, 'TickLabelInterpreter', 'none');

b = barh(ax, stages, 'stacked', 'BarWidth', 0.58);
for idx = 1:numel(b)
    b(idx).FaceColor = colors(idx, :);
    b(idx).EdgeColor = [0.28, 0.28, 0.28];
    b(idx).LineWidth = 0.45;
end

y = 1:numel(labels);
stageTags = {'Issue', 'Status', 'Cert', 'Contract'};
cumStages = cumsum(stages, 2);
for idx = 1:numel(labels)
    text(ax, totals(idx) + max(totals) * 0.025, y(idx), sprintf('%.1f', totals(idx)), ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 7.1, 'Color', [0.20, 0.20, 0.20]);
    for s = 1:size(stages, 2)
        if stages(idx, s) >= max(max(totals) * 0.14, 28)
            left = cumStages(idx, s) - stages(idx, s);
            text(ax, left + stages(idx, s) / 2, y(idx), stageTags{s}, ...
                'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
                'FontName', 'Times New Roman', 'FontSize', 5.8, 'Color', [0.16, 0.16, 0.16]);
        end
    end
end

set(ax, 'YTick', y, 'YTickLabel', labels, 'YDir', 'reverse');
xlabel(ax, 'Latency (ms)', 'Interpreter', 'latex', 'FontSize', 8.8, 'FontWeight', 'bold');
xlim(ax, [0, max(totals) * 1.23]);
ylim(ax, [0.45, numel(labels) + 0.55]);
ax.GridAlpha = 0.18;
text(ax, 0.02, 0.98, panelLabel, 'Units', 'normalized', ...
    'HorizontalAlignment', 'left', 'VerticalAlignment', 'top', ...
    'FontName', 'Times New Roman', 'FontSize', 9.3, 'FontWeight', 'bold', ...
    'Interpreter', 'none', 'BackgroundColor', 'white', 'Margin', 2);
end

function plotCostH(ax, requestLabels, mechanismLabels, values, colors, panelLabel, xLabelText, valueFmt)
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'on');
set(ax, 'LineWidth', 1.0, 'FontSize', 7.6, 'TickLabelInterpreter', 'none');

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
bars = barh(ax, y, flatValues, 'BarWidth', 0.62);
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
        text(ax, flatValues(idx) + maxVal * 0.025, y(idx), sprintf(valueFmt, flatValues(idx)), ...
            'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
            'FontName', 'Times New Roman', 'FontSize', 6.8, 'Color', [0.20, 0.20, 0.20]);
    end
end

set(ax, 'YTick', y, 'YTickLabel', flatLabels, 'YDir', 'reverse');
xlabel(ax, xLabelText, 'Interpreter', 'latex', 'FontSize', 8.8, 'FontWeight', 'bold');
xlim(ax, [0, maxVal * 1.25]);
ylim(ax, [0.12, numel(flatValues) + 0.55]);
ax.GridAlpha = 0.18;
text(ax, 0.02, 0.98, panelLabel, 'Units', 'normalized', ...
    'HorizontalAlignment', 'left', 'VerticalAlignment', 'top', ...
    'FontName', 'Times New Roman', 'FontSize', 9.3, 'FontWeight', 'bold', ...
    'Interpreter', 'none', 'BackgroundColor', 'white', 'Margin', 2);
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
