dpki_alpha = 0.7465;
dpki_eta = 0.2629;
mh21_alpha = 0.2069;
mh21_eta = 0.8066;

% 定义指定的颜色
deep_green = [0, 0.4470, 0.7410];
deep_orange = [1 0.4 0];

% Load the data from the CSV file
data = readtable('tail.csv', 'HeaderLines', 13);
% Extract the relevant data using the generic variable names
DPKI_Time_Value = data.Var2;
DPKI_Sim_Tail_Prob = data.Var3;
DPKI_Approx_Tail_Prob = data.Var4;
MH21_Time_Value = data.Var5;
MH21_Sim_Tail_Prob = data.Var6;
MH21_Approx_Tail_Prob = data.Var7;
Percentile_Data = data.Var1;
% Find the index corresponding to the 70th percentile
[~, start_idx] = min(abs(Percentile_Data - 75));
% Slice all data arrays to start from the 70th percentile
DPKI_Time_Value_sliced = DPKI_Time_Value(start_idx:end);
DPKI_Sim_Tail_Prob_sliced = DPKI_Sim_Tail_Prob(start_idx:end);
DPKI_Approx_Tail_Prob_sliced = DPKI_Approx_Tail_Prob(start_idx:end);
MH21_Time_Value_sliced = MH21_Time_Value(start_idx:end);
MH21_Sim_Tail_Prob_sliced = MH21_Sim_Tail_Prob(start_idx:end);
MH21_Approx_Tail_Prob_sliced = MH21_Approx_Tail_Prob(start_idx:end);
% Create a single figure with two subplots side-by-side
figure;

% --- Left Subplot for DPKI Model ---
subplot(1, 2, 1);
% 仿真线：deep_green
sim_plot_dpki = plot(DPKI_Time_Value_sliced, DPKI_Sim_Tail_Prob_sliced, 'LineWidth', 2, 'Color', deep_green);
hold on;
% 近似线：deep_orange
approx_plot_dpki = plot(DPKI_Time_Value_sliced, DPKI_Approx_Tail_Prob_sliced, '--', 'LineWidth', 2, 'Color', deep_orange);
hold off;
% Add legend to the top-right of the plot
legend([sim_plot_dpki, approx_plot_dpki], 'Simulation', 'Approximation','FontSize', 12, 'Location', 'NorthEast');
% Add the approximation expression to the plot
expr_str = sprintf('$P(T>t_s) \\approx %.2f e^{-%.2ft_{s}}$', dpki_alpha, dpki_eta);
text(0.13, 0.7, expr_str, 'Units', 'normalized', 'FontSize', 13, 'Interpreter', 'latex');
xlabel('Threshold ($t_s$)', 'Interpreter', 'latex','FontSize', 16);
ylabel('$P(T_{b}^{up}>t_{s})$', 'Interpreter', 'latex','FontSize', 16);
grid on;

% --- Right Subplot for M/H2/1 Model ---
subplot(1, 2, 2);
% 仿真线：deep_green
sim_plot_mh21 = plot(MH21_Time_Value_sliced, MH21_Sim_Tail_Prob_sliced, 'LineWidth', 2, 'Color', deep_green);
hold on;
% 近似线：deep_orange
approx_plot_mh21 = plot(MH21_Time_Value_sliced, MH21_Approx_Tail_Prob_sliced, '--', 'LineWidth', 2, 'Color', deep_orange);
hold off;
% Add legend to the top-right of the plot
legend([sim_plot_mh21, approx_plot_mh21], 'Simulation', 'Approximation','FontSize', 12, 'Location', 'NorthEast');
% Add the approximation expression to the plot
expr_str = sprintf('$P(T>t_s) \\approx %.2f e^{-%.2ft_{s}}$', mh21_alpha, mh21_eta);
text(0.13, 0.7, expr_str, 'Units', 'normalized', 'FontSize', 13, 'Interpreter', 'latex');
xlabel('Threshold ($t_s$)', 'Interpreter', 'latex');
ylabel('$P(T_{b}^{low}>t_{s})$', 'Interpreter', 'latex');
grid on;

% Make plots tight to the data
xlim(subplot(1,2,1), [min(DPKI_Time_Value_sliced), max(DPKI_Time_Value_sliced)]);
ylim(subplot(1,2,1), [min(min(DPKI_Sim_Tail_Prob_sliced), min(DPKI_Approx_Tail_Prob_sliced)), max(max(DPKI_Sim_Tail_Prob_sliced), max(DPKI_Approx_Tail_Prob_sliced))]);
xlim(subplot(1,2,2), [min(MH21_Time_Value_sliced), max(MH21_Time_Value_sliced)]);
ylim(subplot(1,2,2), [min(min(MH21_Sim_Tail_Prob_sliced), min(MH21_Approx_Tail_Prob_sliced)), max(max(MH21_Sim_Tail_Prob_sliced), max(MH21_Approx_Tail_Prob_sliced))]);

FIGNAME = 'Fig2';
PrintFigToPaper('-depsc', FIGNAME, 16, 'Times New Roman', 7, 1, 0);