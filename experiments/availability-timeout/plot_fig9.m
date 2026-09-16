clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig9.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);

colors.upper = [0.4660, 0.6740, 0.1880];
colors.lower = [0.0000, 0.4470, 0.7410];
colors.center = [0.8500, 0.3250, 0.0980];
colors.pki = [0.8390, 0.1530, 0.1570];

figure1 = figure('Color', 'w', 'Position', [80, 80, 1380, 860]);
layout = tiledlayout(4, 4, 'TileSpacing', 'compact', 'Padding', 'compact');

ax1 = nexttile(layout, 1, [2 2]);
legendHandles = plotSurfacePanel(ax1, data.respPF, data.respTS, data.respPKI, ...
    data.respLower, data.respUpper, data.respCenter, colors, ...
    '$t_s$');

ax2 = nexttile(layout, 3, [2 2]);
plotSurfacePanel(ax2, data.malPF, data.malTS, data.malPKI, ...
    data.malLower, data.malUpper, data.malCenter, colors, ...
    '$t_s$');

lgd = legend(ax1, legendHandles, ...
    {'DPKI upper', 'DPKI lower', 'DPKI experimental', 'PKI'}, ...
    'Orientation', 'horizontal', 'NumColumns', 4, ...
    'Interpreter', 'none', 'FontSize', 7.6, 'Box', 'off');
lgd.Layout.Tile = 'north';

respSlicePositions = [ ...
    0.060, 0.265, 0.170, 0.165; ...
    0.285, 0.265, 0.170, 0.165; ...
    0.060, 0.055, 0.170, 0.165; ...
    0.285, 0.055, 0.170, 0.165];
malSlicePositions = [ ...
    0.545, 0.265, 0.170, 0.165; ...
    0.770, 0.265, 0.170, 0.165; ...
    0.545, 0.055, 0.170, 0.165; ...
    0.770, 0.055, 0.170, 0.165];
tsSliceTargets = [0.08, 0.10];
pfSliceTargets = [0.20, 0.60];
respSliceAxes = plotMixedTsSliceGroup(figure1, respSlicePositions, data.respPfValues, data.respTsValues, ...
    tsSliceTargets, pfSliceTargets, data.respPKI, data.respLower, data.respUpper, ...
    data.respCenter, colors);
malSliceAxes = plotMixedTsSliceGroup(figure1, malSlicePositions, data.malPfValues, data.malTsValues, ...
    tsSliceTargets, pfSliceTargets, data.malPKI, data.malLower, data.malUpper, ...
    data.malCenter, colors);

drawnow;
addCaption(figure1, ax1, '(a)', 8.0, 0.062, 0.004);
addCaption(figure1, ax2, '(b)', 8.0, 0.062, 0.004);
addCaption(figure1, respSliceAxes, '(c)', 7.8, 0.046, 0.004);
addCaption(figure1, malSliceAxes, '(d)', 7.8, 0.046, 0.004);

set(findall(figure1, '-property', 'FontName'), 'FontName', 'Times New Roman');

outBase = fullfile(currentDir, 'figure');
if exist(fullfile(currentDir, 'PrintFigToPaper.m'), 'file')
    addpath(currentDir);
end

if exist('PrintFigToPaper', 'file')
    PrintFigToPaper('png', outBase, 7.3, 'Times New Roman', 7.3, 1, 0, 1, 5.75, 0);
else
    print(figure1, [outBase '.png'], '-dpng', '-r1200');
end

converterScript = fullfile(currentDir, 'convert_png_to_pdf_eps.py');
cmd = sprintf('python "%s" "%s" 1200', converterScript, outBase);
[status, cmdOut] = system(cmd);
if status ~= 0
    error('PNG-to-PDF-to-EPS conversion failed:\n%s', cmdOut);
end
disp(strtrim(cmdOut));

disp(['Saved figure assets to ' outBase]);

function legendHandles = plotSurfacePanel(ax, PF, TS, PKI, Lower, Upper, Center, colors, yLabelText)
axes(ax); %#ok<LAXES>
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'on');
ax.GridAlpha = 0.22;
ax.LineWidth = 0.6;
ax.TickLabelInterpreter = 'latex';
ax.FontSize = 8;

hPki = surf(ax, PF, TS, PKI, ...
    'FaceColor', colors.pki, 'FaceAlpha', 0.10, ...
    'EdgeColor', 'none');
hLower = surf(ax, PF, TS, Lower, ...
    'FaceColor', colors.lower, 'FaceAlpha', 0.16, ...
    'EdgeColor', 'none');
hUpper = surf(ax, PF, TS, Upper, ...
    'FaceColor', colors.upper, 'FaceAlpha', 0.16, ...
    'EdgeColor', 'none');
hCenter = surf(ax, PF, TS, Center, ...
    'FaceColor', colors.center, 'FaceAlpha', 0.20, ...
    'EdgeColor', 'none');

hX = xlabel(ax, '$p_f$', 'Interpreter', 'latex', 'FontWeight', 'bold');
hY = ylabel(ax, yLabelText, 'Interpreter', 'latex', 'FontWeight', 'bold');
zlabel(ax, '$A$', 'Interpreter', 'latex', 'FontWeight', 'bold');
xlim(ax, [min(PF(:)), max(PF(:))]);
ylim(ax, [min(TS(:)), max(TS(:))]);
zlim(ax, [0, 1]);
view(ax, 43, 26);
set(hX, 'Rotation', -13, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');
set(hY, 'Rotation', 15, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');
ax.XTickLabelRotation = 0;
ax.YTickLabelRotation = 0;
legendHandles = [hUpper, hLower, hCenter, hPki];
end

function axesOut = plotMixedTsSliceGroup(figHandle, positions, pfValues, tsValues, tsSliceTargets, pfSliceTargets, PKI, Lower, Upper, Center, colors)
axesOut = gobjects(1, size(positions, 1));
for ii = 1:size(positions, 1)
    ax = axes('Parent', figHandle, 'Position', positions(ii, :));
    axesOut(ii) = ax;
    hold(ax, 'on');
    box(ax, 'on');
    grid(ax, 'on');
    ax.GridAlpha = 0.20;
    ax.LineWidth = 0.6;
    ax.TickLabelInterpreter = 'latex';
    ax.FontSize = 6.4;

    if ii <= 2
        [~, tsIndex] = min(abs(tsValues - tsSliceTargets(ii)));
        tsTarget = tsValues(tsIndex);
        xValues = pfValues;
        yUpper = Upper(tsIndex, :);
        yLower = Lower(tsIndex, :);
        yCenter = Center(tsIndex, :);
        yPki = PKI(tsIndex, :);
        xlim(ax, [min(pfValues), max(pfValues)]);
        xlabel(ax, '$p_f$', 'Interpreter', 'latex');
        titleText = sprintf('$t_s=%.2f$', tsTarget);
    else
        [~, pfIndex] = min(abs(pfValues - pfSliceTargets(ii - 2)));
        pfTarget = pfValues(pfIndex);
        xValues = tsValues;
        yUpper = Upper(:, pfIndex).';
        yLower = Lower(:, pfIndex).';
        yCenter = Center(:, pfIndex).';
        yPki = PKI(:, pfIndex).';
        xlim(ax, [min(tsValues), max(tsValues)]);
        xlabel(ax, '$t_s$', 'Interpreter', 'latex');
        titleText = sprintf('$p_f=%.1f$', pfTarget);
    end
    plot(ax, xValues, yUpper, '-', ...
        'Color', colors.upper, 'LineWidth', 1.10);
    plot(ax, xValues, yLower, '-', ...
        'Color', colors.lower, 'LineWidth', 1.10);
    plot(ax, xValues, yCenter, '--', ...
        'Color', colors.center, 'LineWidth', 1.20);
    plot(ax, xValues, yPki, '-', ...
        'Color', colors.pki, 'LineWidth', 1.10);

    ylim(ax, [0, 1]);
    text(ax, 0.05, 0.10, titleText, 'Units', 'normalized', ...
        'Interpreter', 'latex', 'FontSize', 6.8, ...
        'HorizontalAlignment', 'left', 'VerticalAlignment', 'bottom', ...
        'BackgroundColor', 'w', 'Margin', 0.1);
    if mod(ii, 2) == 1
        ylabel(ax, '$A$', 'Interpreter', 'latex');
    end
end
end


function addCaption(figHandle, axesHandles, caption, fontSize, yOffset, minY)
positions = collectPositions(axesHandles);
left = min(positions(:, 1));
bottom = min(positions(:, 2));
right = max(positions(:, 1) + positions(:, 3));
width = right - left;
y = max(bottom - yOffset, minY);
annotation(figHandle, 'textbox', [left, y, width, 0.026], ...
    'String', caption, 'Interpreter', 'latex', ...
    'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
    'FontSize', fontSize, 'FontName', 'Times New Roman', ...
    'LineStyle', 'none', 'Margin', 0.1);
end

function positions = collectPositions(axesHandles)
positions = zeros(numel(axesHandles), 4);
for jj = 1:numel(axesHandles)
    positions(jj, :) = get(axesHandles(jj), 'Position');
end
end
