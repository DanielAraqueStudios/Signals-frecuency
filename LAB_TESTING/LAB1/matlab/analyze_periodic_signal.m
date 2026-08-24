function analyze_periodic_signal(csv_path, fs, f_generator_hz)
% ANALYZE_PERIODIC_SIGNAL  FFT + normalized-frequency analysis for LAB1 Part 1.
%
%   analyze_periodic_signal(csv_path, fs, f_generator_hz)
%
%   csv_path        path to a CSV produced by pc_logger/serial_logger.py
%                    in --mode adc (columns: t_s, volts)
%   fs               sampling rate in Hz (500 for LAB1 Part 1)
%   f_generator_hz    the wave generator's configured frequency, used to
%                     compute the calculated normalized frequency f/fs
%
% Prints the values needed for the "Digitalización de señales periódicas"
% table (samples/cycle, calculated vs. observed normalized frequency) and
% saves the FFT magnitude spectrum plot next to the input CSV.
%
% Not executed in this environment: no MATLAB toolchain or real captured
% data was available. Run this once data/periodic_signal/*.csv exists.

    T = readtable(csv_path);
    x = T.volts;
    N = length(x);

    % --- FFT magnitude spectrum ---
    X = fft(x - mean(x)); % remove DC before locating the fundamental peak
    mag = abs(X(1:floor(N/2)+1)) * 2 / N;
    freqs = (0:floor(N/2)) * (fs / N);

    fig = figure('Visible', 'off');
    plot(freqs, mag);
    xlabel('Frecuencia (Hz)');
    ylabel('Magnitud');
    title(sprintf('Espectro FFT - %s', csv_path));
    grid on;
    [out_dir, name, ~] = fileparts(csv_path);
    saveas(fig, fullfile(out_dir, [name '_fft.png']));
    close(fig);

    [~, peak_idx] = max(mag);
    f_observed_peak = freqs(peak_idx);

    % --- samples per cycle (period of the digitized signal) ---
    samples_per_cycle = fs / f_observed_peak;

    % --- normalized frequency: calculated vs. observed ---
    f_norm_calculated = f_generator_hz / fs;
    f_norm_observed = f_observed_peak / fs;
    difference = f_norm_calculated - f_norm_observed;

    fprintf('--- %s ---\n', csv_path);
    fprintf('Frecuencia generador (Hz):        %.4f\n', f_generator_hz);
    fprintf('Frecuencia observada en FFT (Hz):  %.4f\n', f_observed_peak);
    fprintf('Muestras por ciclo:                %.4f\n', samples_per_cycle);
    fprintf('Frecuencia normalizada calculada:  %.6f\n', f_norm_calculated);
    fprintf('Frecuencia normalizada observada:  %.6f\n', f_norm_observed);
    fprintf('Diferencia (calc - obs):           %.6f\n', difference);
end
