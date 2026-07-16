clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig3.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);
intervalsMs = data.intervalsMs(:);
xGridMs = data.xGridMs(:);
expPdf = data.expPdf(:);
sampleCount = data.sampleCount(1);
meanMs = data.meanMs(1);
cv = data.cv(1);
lambdaPerSec = data.lambdaPerSec(1);

figure1 = figure('Color', 'w', 'Position', [80, 80, 740, 740]);
axPdf = axes(figure1, 'Position', [0.17, 0.15, 0.78, 0.81]);
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
PrintFigToPaper('png', outBase, 13, 'Times New Roman', 4.7, 1, 0, 1, 4.7, 0);
PrintFigToPaper('eps', outBase, 13, 'Times New Roman', 4.7, 1, 0, 1, 4.7, 0);
PrintFigToPaper('pdf', outBase, 13, 'Times New Roman', 4.7, 1, 0, 1, 4.7, 0);

disp(['Saved figure assets to ' outBase]);
