clear; clc; close all;

currentDir = fileparts(mfilename('fullpath'));
dataFile = fullfile(currentDir, 'data_fig10.mat');
if ~exist(dataFile, 'file')
    error('Data file not found: %s', dataFile);
end

data = load(dataFile);

colors.upper = [0.4660, 0.6740, 0.1880];
colors.lower = [0.0000, 0.4470, 0.7410];
colors.center = [0.8500, 0.3250, 0.0980];
colors.pki = [0.8390, 0.1530, 0.1570];
colors.band = [0.75, 0.82, 0.90];

figure1 = figure('Color', 'w', 'Position', [80, 80, 1380, 860]);
layout = tiledlayout(4, 4, 'TileSpacing', 'compact', 'Padding', 'compact');

ax1 = nexttile(layout, 1, [2 2]);
legendHandles = plotDiscreteMPanel(ax1, data.respPfValues, data.respMValues, data.respPKI, ...
    data.respLower, data.respUpper, data.respCenter, colors, ...
    true);

ax2 = nexttile(layout, 3, [2 2]);
plotDiscreteMPanel(ax2, data.malPfValues, data.malMValues, data.malPKI, ...
    data.malLower, data.malUpper, data.malCenter, colors, ...
    false);

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
mPairTargets = [4, 5; 11, 12];
pfSliceTargets = [0.40, 0.60];
respSliceAxes = plotMixedMSliceGroup(figure1, respSlicePositions, data.respPfValues, data.respMValues, ...
    mPairTargets, pfSliceTargets, data.respPKI, data.respLower, data.respUpper, ...
    data.respCenter, colors);
malSliceAxes = plotMixedMSliceGroup(figure1, malSlicePositions, data.malPfValues, data.malMValues, ...
    mPairTargets, pfSliceTargets, data.malPKI, data.malLower, data.malUpper, ...
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
    PrintFigToPaper('png', outBase, 7.3, 'Times New Roman', 7.3, 1, 0, 1, 5.85, 0);
    PrintFigToPaper('eps', outBase, 7.3, 'Times New Roman', 7.3, 1, 0, 1, 5.85, 0);
    PrintFigToPaper('pdf', outBase, 7.3, 'Times New Roman', 7.3, 1, 0, 1, 5.85, 0);
else
    print(figure1, [outBase '.png'], '-dpng', '-r1200');
    print(figure1, [outBase '.eps'], '-depsc2', '-loose');
    print(figure1, [outBase '.pdf'], '-dpdf', '-loose', '-r600');
end

disp(['Saved figure assets to ' outBase]);

function legendHandles = plotDiscreteMPanel(ax, pfValues, mValues, PKI, Lower, Upper, Center, colors, showLegend)
axes(ax); %#ok<LAXES>
hold(ax, 'on');
box(ax, 'on');
grid(ax, 'on');
ax.GridAlpha = 0.22;
ax.LineWidth = 0.6;
ax.TickLabelInterpreter = 'latex';
ax.FontSize = 8;

for ii = 1:numel(mValues)
    y = mValues(ii) * ones(size(pfValues));
    fill3(ax, [pfValues, fliplr(pfValues)], [y, fliplr(y)], ...
        [Lower(ii, :), fliplr(Upper(ii, :))], colors.band, ...
        'FaceAlpha', 0.28, 'EdgeColor', 'none');
    hLower = plot3(ax, pfValues, y, Lower(ii, :), '-', ...
        'Color', colors.lower, 'LineWidth', 0.95);
    hUpper = plot3(ax, pfValues, y, Upper(ii, :), '-', ...
        'Color', colors.upper, 'LineWidth', 0.95);
    hCenter = plot3(ax, pfValues, y, Center(ii, :), '--', ...
        'Color', colors.center, 'LineWidth', 1.05);
    hPki = plot3(ax, pfValues, y, PKI(ii, :), '-', ...
        'Color', colors.pki, 'LineWidth', 0.95);
end

hX = xlabel(ax, '$p_f$', 'Interpreter', 'latex', 'FontWeight', 'bold');
hY = ylabel(ax, '$M$', 'Interpreter', 'latex', 'FontWeight', 'bold');
zlabel(ax, '$A$', 'Interpreter', 'latex', 'FontWeight', 'bold');
xlim(ax, [min(pfValues), max(pfValues)]);
ylim(ax, [min(mValues), max(mValues)]);
zlim(ax, [0, 1]);
yticks(ax, mValues);
view(ax, 43, 26);
set(hX, 'Rotation', -13, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');
set(hY, 'Rotation', 15, 'VerticalAlignment', 'middle', 'HorizontalAlignment', 'center');
ax.XTickLabelRotation = 0;
ax.YTickLabelRotation = 0;
legendHandles = [hUpper, hLower, hCenter, hPki];
if ~showLegend
    legendHandles = [hUpper, hLower, hCenter, hPki];
end
end

function axesOut = plotMixedMSliceGroup(figHandle, positions, pfValues, mValues, mPairTargets, pfSliceTargets, PKI, Lower, Upper, Center, colors)
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
        rowIdx = arrayfun(@(target) nearestIndex(mValues, target), mPairTargets(ii, :));
        xlim(ax, [min(pfValues), max(pfValues)]);
        xlabel(ax, '$p_f$', 'Interpreter', 'latex');
        titleText = sprintf('$M=%d,%d$', round(mValues(rowIdx(1))), round(mValues(rowIdx(2))));
        markerStyle = {'d', 'd'};
        for jj = 1:numel(rowIdx)
            plotMechanismLines(ax, pfValues, Upper(rowIdx(jj), :), Lower(rowIdx(jj), :), ...
                Center(rowIdx(jj), :), PKI(rowIdx(jj), :), colors, markerStyle{jj});
        end
    else
        pfTarget = pfSliceTargets(ii - 2);
        xValues = mValues;
        yUpper = interp1(pfValues(:), Upper', pfTarget, 'linear');
        yLower = interp1(pfValues(:), Lower', pfTarget, 'linear');
        yCenter = interp1(pfValues(:), Center', pfTarget, 'linear');
        yPki = interp1(pfValues(:), PKI', pfTarget, 'linear');
        xlim(ax, [min(mValues), max(mValues)]);
        xticks(ax, [min(mValues), round(mean(mValues)), max(mValues)]);
        xlabel(ax, '$M$', 'Interpreter', 'latex');
        titleText = sprintf('$p_f=%.1f$', pfTarget);
        plotMechanismLines(ax, xValues, yUpper, yLower, yCenter, yPki, colors, 'd');
    end
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

function idx = nearestIndex(values, target)
[~, idx] = min(abs(values - target));
end

function plotMechanismLines(ax, xValues, yUpper, yLower, yCenter, yPki, colors, markerStyle)
markerSize = 1.00;
plot(ax, xValues, yUpper, '-', ...
    'Color', colors.upper, 'LineWidth', 1.10);
plot(ax, xValues, yLower, '-', ...
    'Color', colors.lower, 'LineWidth', 1.10);
plot(ax, xValues, yCenter, '--', ...
    'Color', colors.center, 'LineWidth', 1.20, ...
    'Marker', markerStyle, 'MarkerSize', markerSize);
plot(ax, xValues, yPki, '-', ...
    'Color', colors.pki, 'LineWidth', 1.10);
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
