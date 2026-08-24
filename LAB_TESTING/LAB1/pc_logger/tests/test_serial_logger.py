import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serial_logger import (
    FRAME_FORMATS,
    adc_decode,
    imu_decode,
    encoder_decode,
    parse_stream,
    ADC_MAX_CODE,
    ADC_REF_VOLTS,
)


def reader_from_bytes(data: bytes):
    buf = io.BytesIO(data)

    def read(n):
        return buf.read(n)

    return read


class TestAdcDecode:
    def test_zero_code_is_zero_volts(self):
        payload = struct.pack("<H", 0)
        assert adc_decode(payload) == (0.0,)

    def test_full_scale_code_is_ref_volts(self):
        payload = struct.pack("<H", ADC_MAX_CODE)
        (volts,) = adc_decode(payload)
        assert abs(volts - ADC_REF_VOLTS) < 1e-9

    def test_midscale_is_half_ref(self):
        payload = struct.pack("<H", ADC_MAX_CODE // 2)
        (volts,) = adc_decode(payload)
        assert abs(volts - ADC_REF_VOLTS / 2) < 0.01


class TestImuDecode:
    def test_all_zero_raw_gives_zero_physical(self):
        payload = struct.pack("<6h", 0, 0, 0, 0, 0, 0)
        values = imu_decode(payload)
        assert all(abs(v) < 1e-9 for v in values)

    def test_one_g_accel_converts_to_gravity(self):
        payload = struct.pack("<6h", 16384, 0, 0, 0, 0, 0)
        values = imu_decode(payload)
        assert abs(values[0] - 9.80665) < 0.01

    def test_negative_values_roundtrip(self):
        payload = struct.pack("<6h", -16384, 0, 0, 0, 0, 0)
        values = imu_decode(payload)
        assert abs(values[0] + 9.80665) < 0.01


class TestEncoderDecode:
    def test_zero_pulses_zero_velocity(self):
        payload = struct.pack("<hH", 0, 0)
        delta, velocity = encoder_decode(payload, pulses_per_rev=100)
        assert delta == 0.0
        assert velocity == 0.0

    def test_full_revolution_worth_of_pulses(self):
        payload = struct.pack("<hH", 100, 0)
        delta, velocity = encoder_decode(payload, pulses_per_rev=100)
        assert abs(delta - 2 * 3.141592653589793) < 1e-6

    def test_raises_without_pulses_per_rev(self):
        payload = struct.pack("<hH", 10, 0)
        try:
            encoder_decode(payload, pulses_per_rev=0)
            assert False, "expected ValueError"
        except ValueError:
            pass


class TestParseStream:
    def test_single_adc_frame(self):
        frame_format = FRAME_FORMATS["adc"]
        data = bytes([0xA5]) + struct.pack("<H", 2048)
        results = list(parse_stream(reader_from_bytes(data), frame_format, adc_decode))
        assert len(results) == 1

    def test_skips_garbage_before_sync_byte(self):
        frame_format = FRAME_FORMATS["adc"]
        garbage = bytes([0x00, 0xFF, 0x12])
        data = garbage + bytes([0xA5]) + struct.pack("<H", 100)
        results = list(parse_stream(reader_from_bytes(data), frame_format, adc_decode))
        assert len(results) == 1

    def test_multiple_frames(self):
        frame_format = FRAME_FORMATS["adc"]
        data = b"".join(bytes([0xA5]) + struct.pack("<H", code) for code in (0, 1000, 4095))
        results = list(parse_stream(reader_from_bytes(data), frame_format, adc_decode))
        assert len(results) == 3

    def test_truncated_final_frame_is_dropped(self):
        frame_format = FRAME_FORMATS["adc"]
        data = bytes([0xA5]) + struct.pack("<H", 100) + bytes([0xA5, 0x01])  # incomplete 2nd frame
        results = list(parse_stream(reader_from_bytes(data), frame_format, adc_decode))
        assert len(results) == 1

    def test_empty_stream_yields_nothing(self):
        frame_format = FRAME_FORMATS["adc"]
        results = list(parse_stream(reader_from_bytes(b""), frame_format, adc_decode))
        assert results == []
