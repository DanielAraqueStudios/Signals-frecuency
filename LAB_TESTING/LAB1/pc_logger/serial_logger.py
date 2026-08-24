"""Efficient serial-to-CSV logger for the LAB1 firmware sketches.

Reads the fixed-size binary frames produced by firmware/part*/*.ino,
converts raw ADC/sensor codes to physical units, and appends rows straight
to a CSV file on disk -- no plotting, no visualization, per the assignment
("NO lleve a cabo visualizaciones y/o graficas").

Usage:
    python serial_logger.py --mode adc      --port COM5 --baud 115200 --out data/periodic_signal/signal_50hz.csv
    python serial_logger.py --mode bme280   --port COM5 --baud 115200 --out data/bme280_baseline/bme280_baseline.csv
    python serial_logger.py --mode encoder  --port COM5 --baud 115200 --out data/encoder/encoder_5v.csv

Each mode matches one sync byte and frame size documented in
firmware/README.md:
    adc     (part1/part2 sketches):    sync 0xA5, 3-byte frame, 1 channel
    bme280  (part3_bme280_sensor):     sync 0xB6, 13-byte frame, 3 channels (already physical units)
    encoder (part3_encoder_motor):     sync 0xC5, 5-byte frame, 1 channel

No physical hardware was available to run this end-to-end in this
environment; the framing/parsing logic mirrors the .ino sources exactly
and is exercised by tests/test_serial_logger.py against synthetic byte
streams, not a live serial port.
"""

from __future__ import annotations

import argparse
import csv
import struct
import sys
import time

ADC_REF_VOLTS = 3.3
ADC_MAX_CODE = 4095

ENCODER_SAMPLE_PERIOD_S = 0.005  # 5 ms, must match part3_encoder_motor.ino


class FrameFormat:
    """Sync byte, frame size, and (raw tuple -> physical-unit tuple) mapping."""

    def __init__(self, sync: int, size: int, field_names: list[str], decode):
        self.sync = sync
        self.size = size
        self.field_names = field_names
        self.decode = decode


def adc_decode(payload: bytes) -> tuple[float]:
    code = struct.unpack_from("<H", payload, 0)[0]
    volts = (code / ADC_MAX_CODE) * ADC_REF_VOLTS
    return (volts,)


def bme280_decode(payload: bytes) -> tuple[float, float, float]:
    """Unpack the three floats the BME280 sketch already compensated on-device.

    Unlike adc_decode/encoder_decode, no unit conversion happens here: the
    firmware sends temperature (deg C), pressure (hPa), and humidity (%RH)
    directly, since the compensation formulas need per-sensor factory
    calibration coefficients that live on the ESP32, not fixed constants.
    """
    temperature_c, pressure_hpa, humidity_pct = struct.unpack_from("<3f", payload, 0)
    return (temperature_c, pressure_hpa, humidity_pct)


def encoder_decode(payload: bytes, pulses_per_rev: int) -> tuple[float, float]:
    pulse_count = struct.unpack_from("<h", payload, 0)[0]
    if pulses_per_rev <= 0:
        raise ValueError("pulses_per_rev must be set (see firmware/part3_encoder_motor.ino)")
    delta_rad = (pulse_count / pulses_per_rev) * 2 * 3.141592653589793
    velocity_rad_s = delta_rad / ENCODER_SAMPLE_PERIOD_S
    return (delta_rad, velocity_rad_s)


FRAME_FORMATS = {
    "adc": FrameFormat(0xA5, 3, ["volts"], adc_decode),
    "bme280": FrameFormat(
        0xB6, 13,
        ["temperature_c", "pressure_hpa", "humidity_pct"],
        bme280_decode,
    ),
    # encoder_decode needs pulses_per_rev, bound via functools.partial in main()
    "encoder": FrameFormat(0xC5, 5, ["delta_angle_rad", "angular_velocity_rads"], None),
}


def parse_stream(read_bytes, frame_format: FrameFormat, decode_fn):
    """Yield decoded field tuples from a byte-stream reader, resyncing on the sync byte.

    ``read_bytes(n)`` must return up to ``n`` bytes (like a file/serial
    object's ``.read``), or b"" at end of stream.
    """
    payload_size = frame_format.size - 1
    while True:
        sync = read_bytes(1)
        if not sync:
            return
        if sync[0] != frame_format.sync:
            continue  # resync: drop stray bytes until the next sync byte
        payload = read_bytes(payload_size)
        if len(payload) < payload_size:
            return  # truncated frame at end of stream
        yield decode_fn(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="LAB1 serial-to-CSV logger (no plotting)")
    parser.add_argument("--mode", choices=["adc", "bme280", "encoder"], required=True)
    parser.add_argument("--port", required=True, help="e.g. COM5 or /dev/ttyACM0")
    parser.add_argument("--baud", type=int, required=True)
    parser.add_argument("--out", required=True, help="output CSV path")
    parser.add_argument("--duration", type=float, default=None, help="seconds to capture; omit to run until Ctrl+C")
    parser.add_argument("--pulses-per-rev", type=int, default=0, help="required for --mode encoder")
    args = parser.parse_args()

    import serial  # pyserial; imported lazily so --help works without it installed

    frame_format = FRAME_FORMATS[args.mode]
    if args.mode == "encoder":
        decode_fn = lambda payload: encoder_decode(payload, args.pulses_per_rev)
    else:
        decode_fn = frame_format.decode

    with serial.Serial(args.port, args.baud, timeout=1) as ser, open(args.out, "w", newline="") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(["t_s"] + frame_format.field_names)

        start = time.perf_counter()
        count = 0
        for values in parse_stream(ser.read, frame_format, decode_fn):
            t = time.perf_counter() - start
            writer.writerow([f"{t:.6f}"] + [f"{v:.6f}" for v in values])
            count += 1
            if args.duration is not None and t >= args.duration:
                break

    print(f"Wrote {count} samples to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
