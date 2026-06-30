clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig3.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);
headers = localCellColumn(data.headers);
rows = localCellMatrix(data.rows);
colWidths = data.colWidths(:)' / sum(data.colWidths(:));

intervalsMs = data.intervalsMs(:);
xGridMs = data.xGridMs(:);
expPdf = data.expPdf(:);
sampleCount = data.sampleCount(1);
meanMs = data.meanMs(1);
cv = data.cv(1);
lambdaPerSec = data.lambdaPerSec(1);

figure1 = figure('Color', 'w', 'Position', [80, 80, 1480, 620]);
t = tiledlayout(figure1, 1, 2, 'Padding', 'compact', 'TileSpacing', 'compact');

axTable = nexttile(t, 1);
axis(axTable, [0, 1, 0, 1]);
axis(axTable, 'off');
hold(axTable, 'on');

leftMargin = 0.02;
rightMargin = 0.02;
bottomMargin = 0.04;
topMargin = 0.10;
tableWidth = 1 - leftMargin - rightMargin;
tableHeight = 1 - bottomMargin - topMargin;
headerHeight = 0.105;
bodyHeight = (tableHeight - headerHeight) / size(rows, 1);
xStarts = leftMargin + tableWidth * [0, cumsum(colWidths(1:end-1))];
xWidths = tableWidth * colWidths;
yTop = 1 - topMargin;

text(0.0, 0.985, '(a) Model-level prototype inputs', ...
    'FontName', 'Times New Roman', 'FontSize', 11.2, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'left', 'VerticalAlignment', 'top', 'Interpreter', 'none');

headerColor = [207, 221, 241] / 255;
rowA = [248, 250, 253] / 255;
rowB = [238, 244, 252] / 255;

for c = 1:numel(headers)
    y = yTop - headerHeight;
    rectangle('Position', [xStarts(c), y, xWidths(c), headerHeight], ...
        'FaceColor', headerColor, 'EdgeColor', [0.20, 0.20, 0.20], 'LineWidth', 0.9);
    text(xStarts(c) + xWidths(c) / 2, y + headerHeight / 2, headers{c}, ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
        'FontName', 'Times New Roman', 'FontSize', 8.2, 'FontWeight', 'bold', ...
        'Interpreter', 'none');
end

for r = 1:size(rows, 1)
    y = yTop - headerHeight - r * bodyHeight;
    fillColor = rowA;
    if mod(r, 2) == 0
        fillColor = rowB;
    end
    for c = 1:numel(headers)
        rectangle('Position', [xStarts(c), y, xWidths(c), bodyHeight], ...
            'FaceColor', fillColor, 'EdgeColor', [0.55, 0.55, 0.55], 'LineWidth', 0.55);
        if c == 1
            xText = xStarts(c) + xWidths(c) / 2;
            hAlign = 'center';
            interpreter = 'latex';
            fontSize = 8.4;
        else
            xText = xStarts(c) + 0.012;
            hAlign = 'left';
            interpreter = 'none';
            fontSize = 7.05;
        end
        text(xText, y + bodyHeight / 2, rows{r, c}, ...
            'HorizontalAlignment', hAlign, 'VerticalAlignment', 'middle', ...
            'FontName', 'Times New Roman', 'FontSize', fontSize, ...
            'Interpreter', interpreter);
    end
end

axPdf = nexttile(t, 2);
hold(axPdf, 'on');
box(axPdf, 'on');
grid(axPdf, 'on');
set(axPdf, 'LineWidth', 1.1, 'FontSize', 10.5, 'TickLabelInterpreter', 'latex');

histogram(axPdf, intervalsMs, 50, ...
    'Normalization', 'pdf', ...
    'FaceColor', [205, 226, 232] / 255, ...
    'EdgeColor', 'white', ...
    'LineWidth', 0.45, ...
    'DisplayName', 'Prototype PDF');

plot(axPdf, xGridMs, expPdf, '-', ...
    'Color', [245, 151, 144] / 255, ...
    'LineWidth', 2.2, ...
    'DisplayName', 'Exponential fit');

xlabel(axPdf, 'Inter-block interval (ms)', 'Interpreter', 'latex', 'FontSize', 11.5, 'FontWeight', 'bold');
ylabel(axPdf, 'PDF', 'Interpreter', 'latex', 'FontSize', 11.5, 'FontWeight', 'bold');
axPdf.GridAlpha = 0.22;
xMax = max(xGridMs);
yMax = max([expPdf; ylim(axPdf)']);
xlim(axPdf, [0, xMax]);
ylim(axPdf, [0, yMax * 1.09]);

text(axPdf, 0.02, 1.05, '(b) PoW inter-block interval', ...
    'Units', 'normalized', 'FontName', 'Times New Roman', ...
    'FontSize', 11.2, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'left', 'VerticalAlignment', 'bottom', 'Interpreter', 'none');

annotationText = {
    sprintf('N = %d', round(sampleCount))
    sprintf('Mean = %.1f ms', meanMs)
    sprintf('CV = %.3f', cv)
    sprintf('$\\hat{\\lambda}_p$ = %.2f s$^{-1}$', lambdaPerSec)
};
text(axPdf, xMax * 0.62, yMax * 0.88, annotationText, ...
    'Interpreter', 'latex', ...
    'FontSize', 8.4, ...
    'BackgroundColor', 'white', ...
    'Margin', 5, ...
    'EdgeColor', [0.85, 0.85, 0.85], ...
    'VerticalAlignment', 'top');

legend(axPdf, 'Location', 'northeast', 'Interpreter', 'none', 'Box', 'off', 'FontSize', 8.8);

outBase = fullfile(currentDir, 'figure');
addpath(currentDir);
PrintFigToPaper('png', outBase, 13, 'Times New Roman', 7.4, 1, 0, 1, 4.7, 0);
PrintFigToPaper('eps', outBase, 13, 'Times New Roman', 7.4, 1, 0, 1, 4.7, 0);
PrintFigToPaper('pdf', outBase, 13, 'Times New Roman', 7.4, 1, 0, 1, 4.7, 0);

disp(['Saved figure assets to ' outBase]);

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

function out = localCellMatrix(raw)
out = cell(size(raw));
for r = 1:size(raw, 1)
    for c = 1:size(raw, 2)
        out{r, c} = char(string(raw{r, c}));
    end
end
end
