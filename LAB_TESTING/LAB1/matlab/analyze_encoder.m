function analyze_encoder(csv_path, fs, applied_voltage)
% ANALYZE_ENCODER  Velocity statistics + FFT bandwidth for LAB1 Part 3 (encoder/motor).
%
%   analyze_encoder(csv_path, fs, applied_voltage)
%
%   csv_path          path to a CSV produced by pc_logger/serial_logger.py
%                      in --mode encoder (columns: t_s, delta_angle_rad,
%                      angular_velocity_rads)
%   fs                 sampling rate in Hz (200 for LAB1 Part 3)
%   applied_voltage    the constant voltage applied to the motor for this
%                      run, only used to label the printed row
%
% Prints mean velocity, standard deviation, and -3 dB bandwidth -- the
% values needed for the "Voltaje aplicado / Velocidad promedio / ..." table.
%
% Not executed in this environment: no MATLAB toolchain, motor, or real
% captured data was available. Run this once data/encoder/*.csv exists.

    T = readtable(csv_path);
    velocity = T.angular_velocity_rads;
    N = length(velocity);

    mu = mean(velocity);
    sigma = std(velocity);

    X = fft(velocity - mu);
    mag = abs(X(1:floor(N/2)+1)) * 2 / N;
    freqs = (0:floor(N/2)) * (fs / N);

    peak_mag = max(mag);
    above_half_power = freqs(mag >= peak_mag / sqrt(2));
    if isempty(above_half_power)
        bandwidth_hz = 0;
    else
        bandwidth_hz = max(above_half_power);
    end

    fprintf('--- %s (V = %.2f V) ---\n', csv_path, applied_voltage);
    fprintf('Velocidad promedio (rad/s): %.4f\n', mu);
    fprintf('Desviacion estandar (rad/s): %.4f\n', sigma);
    fprintf('Ancho de banda (Hz):        %.4f\n', bandwidth_hz);
end
