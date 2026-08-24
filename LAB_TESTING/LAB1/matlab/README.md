# LAB1 MATLAB analysis scripts

Four functions, one per data type produced by `pc_logger/serial_logger.py`.
None have been run in this environment — no MATLAB toolchain and no real
captured data were available. Run them once the corresponding `data/*/`
folder has real CSVs.

| Script | Input | Produces |
|---|---|---|
| `analyze_periodic_signal.m` | `data/periodic_signal/*.csv` (`--mode adc`) | FFT plot (saved as PNG) + samples/cycle, calculated vs. observed normalized frequency, for the Part 1 table. |
| `analyze_imu.m` | `data/imu_still/*.csv`, `data/imu_moving/*.csv` (`--mode imu`) | Mean, std, DC level, −3 dB bandwidth per of the 6 channels, for the Part 3 IMU tables. |
| `analyze_encoder.m` | `data/encoder/*.csv` (`--mode encoder`) | Mean velocity, std, −3 dB bandwidth, for the Part 3 encoder/motor table. |
| `analyze_aliasing.m` | `data/aliasing/*.csv` (`--mode adc`, generator frequency ≥ `fs`) | Calculated (folded) vs. observed normalized frequency, and the reconstructed-signal frequency, for the optional aliasing table. |

Example:

```matlab
analyze_periodic_signal('../data/periodic_signal/signal_50hz.csv', 500, 50);
analyze_imu('../data/imu_still/imu_still.csv', 200);
analyze_encoder('../data/encoder/encoder_5v.csv', 200, 5.0);
analyze_aliasing('../data/aliasing/signal_550hz.csv', 500, 550);
```
