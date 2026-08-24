function analyze_bme280(csv_path, fs)
% ANALYZE_BME280  Statistics + FFT bandwidth per channel for LAB1 Part 3 (BME280).
%
%   analyze_bme280(csv_path, fs)
%
%   csv_path   path to a CSV produced by pc_logger/serial_logger.py in
%              --mode bme280 (columns: t_s, temperature_c, pressure_hpa, humidity_pct)
%   fs          sampling rate in Hz (100 for LAB1 Part 3 -- see
%               firmware/part3_bme280_sensor/part3_bme280_sensor.ino for
%               why the BME280 cannot sustain the 200 Hz used by the
%               encoder stage)
%
% For each of the 3 channels, prints mean, standard deviation, and
% -3 dB bandwidth from the FFT magnitude spectrum -- the values needed
% for the "condiciones base" / "condiciones perturbadas" result tables.
%
% Not executed in this environment: no MATLAB toolchain or real captured
% data was available. Run this once data/bme280_baseline/*.csv and
% data/bme280_perturbed/*.csv exist.

    T = readtable(csv_path);
    channel_names = {'temperature_c', 'pressure_hpa', 'humidity_pct'};

    fprintf('--- %s ---\n', csv_path);
    fprintf('%-15s %10s %10s %10s %12s\n', 'Canal', 'Media', 'DesvEst', 'NivelDC', 'AnchoBanda(Hz)');

    for i = 1:numel(channel_names)
        x = T.(channel_names{i});
        N = length(x);

        mu = mean(x);
        sigma = std(x);

        X = fft(x - mu);
        mag = abs(X(1:floor(N/2)+1)) * 2 / N;
        freqs = (0:floor(N/2)) * (fs / N);

        peak_mag = max(mag);
        above_half_power = freqs(mag >= peak_mag / sqrt(2)); % -3 dB threshold
        if isempty(above_half_power)
            bandwidth_hz = 0;
        else
            bandwidth_hz = max(above_half_power);
        end

        fprintf('%-15s %10.4f %10.4f %10.4f %12.4f\n', channel_names{i}, mu, sigma, mu, bandwidth_hz);
    end
end
