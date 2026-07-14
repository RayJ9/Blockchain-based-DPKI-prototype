function [] = PrintFigToPaper(OutputType, plotFileName, ...
    FigFontSize, FigFontName, FigWidth, IsPrint, IsPrintTime, ...
    IsCustomHeight, FigHeightCustom, IsHideAxis)
% Standardized MATLAB figure export helper for academic paper figures.
%
% Parameters:
%   OutputType      export format, such as "png", "pdf", "eps", "-dpng"
%   plotFileName    output path without extension
%   FigFontSize     target font size, for example 16
%   FigFontName     target font name, for example 'Times New Roman'
%   FigWidth        width in inches
%   IsPrint         1 to export, 0 to only normalize styling
%   IsPrintTime     1 to append a timestamp suffix
%   IsCustomHeight  1 to use FigHeightCustom
%   FigHeightCustom custom height in inches
%   IsHideAxis      1 to hide axis colors

if nargin < 6, IsPrint = 1; end
if nargin < 7, IsPrintTime = 0; end
if nargin < 8, IsCustomHeight = 0; end
if nargin < 9, FigHeightCustom = 0; end
if nargin < 10, IsHideAxis = 0; end

if ~ishandle(gcf)
    error('No current figure to print.');
end
if FigWidth <= 0
    error('FigWidth must be positive.');
end

figHandle = gcf;
set(figHandle, 'Renderer', 'painters');
set(figHandle, 'PaperUnits', 'inches');
set(figHandle, 'Units', 'inches');
set(figHandle, 'PaperPositionMode', 'auto');

ax = gca;
if IsHideAxis == 1
    set(ax, 'XColor', 'none', 'YColor', 'none');
else
    set(ax, 'Color', 'none');
end

screenPosition = get(figHandle, 'Position');
FigHeight = FigWidth / screenPosition(3) * screenPosition(4);
if IsCustomHeight == 1
    FigHeight = FigHeightCustom;
end

set(figHandle, 'PaperPosition', [0 0 FigWidth FigHeight]);
set(figHandle, 'Position', [screenPosition(1:2) / 2, FigWidth, FigHeight]);

set([ax.XLabel, ax.YLabel, ax.Title], 'FontName', FigFontName);
set(findobj(ax, 'FontName', 'Helvetica'), 'FontName', FigFontName);

fontTargets = [10, 12, 14, 16];
for idx = 1:numel(fontTargets)
    set(findobj(ax, 'FontSize', fontTargets(idx)), 'FontSize', FigFontSize);
end

if IsPrint ~= 1
    return;
end

if IsPrintTime == 1
    baseName = [plotFileName, datestr(clock, 30)];
else
    baseName = plotFileName;
end

formatName = lower(strrep(OutputType, '-', ''));
vectorDpi = 600;
rasterDpi = 1200;

switch formatName
    case 'png'
        print(figHandle, baseName, '-dpng', ['-r', num2str(rasterDpi)]);
    case 'eps'
        print(figHandle, baseName, '-depsc2', '-loose');
    case 'pdf'
        print(figHandle, baseName, '-dpdf', '-loose', ['-r', num2str(vectorDpi)]);
    otherwise
        print(figHandle, baseName, ['-d', formatName], ['-r', num2str(vectorDpi)]);
end
end
