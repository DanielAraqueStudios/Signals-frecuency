function analyze_aliasing(csv_path, fs, f_generator_hz)
% ANALYZE_ALIASING  Normalized-frequency + folded-frequency analysis for
% the optional "Fenomeno de aliasing" section of LAB1.
%
%   analyze_aliasing(csv_path, fs, f_generator_hz)
%
%   csv_path         path to a CSV produced by pc_logger/serial_logger.py
%                     in --mode adc (columns: t_s, volts)
%   fs                sampling rate in Hz (500, unchanged from Part 1)
%   f_generator_hz     the wave generator's configured frequency, which for
%                      this section is intentionally >= fs
%
% Computes the calculated normalized frequency (folded into [0, 0.5] per
% the sampling theorem when f_generator_hz > fs/2) and the frequency
% observed in the FFT of the captured (aliased) signal, plus the implied
% frequency of the reconstructed signal on the oscilloscope
% (f_reconstructed = f_observed_normalized * fs) -- the four columns
% needed for the aliasing table.
%
% Not executed in this environment: no MATLAB toolchain, wave generator,
% oscilloscope, or real captured data was available. Run this once
% data/aliasing/*.csv exists.

    T = readtable(csv_path);
    x = T.volts;
    N = length(x);

    X = fft(x - mean(x));
    mag = abs(X(1:floor(N/2)+1)) * 2 / N;
    freqs = (0:floor(N/2)) * (fs / N);

    [~, peak_idx] = max(mag);
    f_observed_peak = freqs(peak_idx);
    f_norm_observed = f_observed_peak / fs;

    % Theoretical folded (aliased) normalized frequency: fold f_generator_hz
    % into [0, fs/2] by reflecting around multiples of fs/2, per the
    % sampling theorem's aliasing relationship.
    f_folded = mod(f_generator_hz, fs);
    if f_folded > fs / 2
        f_folded = fs - f_folded;
    end
    f_norm_calculated = f_folded / fs;

    f_reconstructed_hz = f_norm_observed * fs;

    fprintf('--- %s ---\n', csv_path);
    fprintf('Frecuencia analoga (Hz):                  %.4f\n', f_generator_hz);
    fprintf('Frecuencia normalizada calculada:          %.6f\n', f_norm_calculated);
    fprintf('Frecuencia normalizada observada:          %.6f\n', f_norm_observed);
    fprintf('Frecuencia de la senal reconstruida (Hz):  %.4f\n', f_reconstructed_hz);
end
