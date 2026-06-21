clear; clc; close all;

theory_data = readtable('theory_results_by_epsilon.csv');
sim_data = readtable('simulation_results_by_epsilon.csv');

epsilon = theory_data.epsilon;
theory_DPKI_upper = theory_data.DPKI_upper_theory;
theory_DPKI_lower = theory_data.DPKI_lower_theory;
theory_PKI = theory_data.PKI_theory;

sim_epsilon = sim_data.epsilon;
sim_DPKI = sim_data.DPKI_sim;
sim_PKI = sim_data.PKI_sim;

figure;
hold on;

plot(epsilon, theory_DPKI_upper, '--', 'Color', [0 0.5 0], ...
     'LineWidth', 1.5, 'DisplayName', 'DPKI Upper Bound');
plot(epsilon, theory_DPKI_lower, '--', 'Color', [0, 0.4470, 0.7410], ...
     'LineWidth', 1.5, 'DisplayName', 'DPKI Lower Bound');

valid_DPKI_idx = ~isnan(sim_DPKI);
plot(sim_epsilon(valid_DPKI_idx), sim_DPKI(valid_DPKI_idx), '-o', ...
     'Color', [1 0.4 0], 'LineWidth', 1.5, 'MarkerSize', 4, ...
     'MarkerEdgeColor', [1 0.4 0], 'MarkerFaceColor', [1 0.4 0], ...
     'DisplayName', 'DPKI Experimental');
plot(epsilon, theory_PKI, '-', 'Color', [0.85 0 0], ...
     'LineWidth', 1.2, 'HandleVisibility', 'off');
valid_PKI_idx = ~isnan(sim_PKI);
plot(sim_epsilon(valid_PKI_idx), sim_PKI(valid_PKI_idx), '-o', ...
     'Color', [0.85 0 0], 'LineWidth', 1.5, 'MarkerSize', 4, ...
     'MarkerEdgeColor', [0.85 0 0], 'MarkerFaceColor', [0.85 0 0], ...
     'DisplayName', 'PKI Analytical/Experimental');

xlabel('$\epsilon$', 'Interpreter', 'latex');
ylabel('$E[T]$', 'Interpreter', 'latex');
legend('Location', 'northwest', 'Interpreter', 'latex', 'FontSize', 10);
grid on;
xlim([min(epsilon), max(epsilon)]);
xticks(min(epsilon):0.1:max(epsilon));
hold off;
box on;

print(gcf, '-depsc', 'Fig3_epsilon_ET.eps');
print(gcf, '-dpng', '-r300', 'Fig3_epsilon_ET.png');
