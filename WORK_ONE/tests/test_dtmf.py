"""Unit tests for dtmf_dialer.dtmf.

Covers pure signal-generation and file-writing logic. `play_wav` is not
tested here since it triggers real audio playback via `winsound`.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dtmf_dialer.dtmf import (
    DTMF_FREQUENCIES,
    generate_dtmf_sequence,
    generate_silence,
    generate_tone,
    save_wav,
)

SAMPLE_RATE = 44100


class TestDtmfFrequencies:
    def test_covers_all_ten_digits(self):
        assert set(DTMF_FREQUENCIES) == set("0123456789")

    def test_known_digit_pairs_match_itu_t_standard(self):
        assert DTMF_FREQUENCIES["1"] == (697, 1209)
        assert DTMF_FREQUENCIES["5"] == (770, 1336)
        assert DTMF_FREQUENCIES["0"] == (941, 1336)


class TestGenerateTone:
    def test_sample_count_matches_duration(self):
        samples = generate_tone(697, 1209, duration_s=0.5, sample_rate=SAMPLE_RATE)
        assert len(samples) == int(SAMPLE_RATE * 0.5)

    def test_output_dtype_is_int16(self):
        samples = generate_tone(697, 1209, duration_s=0.1, sample_rate=SAMPLE_RATE)
        assert samples.dtype == np.int16

    def test_amplitude_stays_within_int16_range(self):
        samples = generate_tone(697, 1209, duration_s=0.5, sample_rate=SAMPLE_RATE)
        assert samples.min() >= -32768
        assert samples.max() <= 32767

    def test_zero_duration_yields_no_samples(self):
        samples = generate_tone(697, 1209, duration_s=0.0, sample_rate=SAMPLE_RATE)
        assert len(samples) == 0

    def test_different_frequencies_yield_different_tones(self):
        tone_1 = generate_tone(697, 1209, duration_s=0.1, sample_rate=SAMPLE_RATE)
        tone_2 = generate_tone(770, 1336, duration_s=0.1, sample_rate=SAMPLE_RATE)
        assert not np.array_equal(tone_1, tone_2)


class TestGenerateSilence:
    def test_sample_count_matches_duration(self):
        silence = generate_silence(duration_s=0.05, sample_rate=SAMPLE_RATE)
        assert len(silence) == int(SAMPLE_RATE * 0.05)

    def test_all_samples_are_zero(self):
        silence = generate_silence(duration_s=0.05, sample_rate=SAMPLE_RATE)
        assert np.all(silence == 0)


class TestGenerateDtmfSequence:
    def test_single_digit_length_is_tone_plus_pause(self):
        sequence = generate_dtmf_sequence("1", tone_duration_s=0.5, pause_duration_s=0.05, sample_rate=SAMPLE_RATE)
        expected_len = int(SAMPLE_RATE * 0.5) + int(SAMPLE_RATE * 0.05)
        assert len(sequence) == expected_len

    def test_multi_digit_length_scales_linearly(self):
        sequence = generate_dtmf_sequence("123", tone_duration_s=0.5, pause_duration_s=0.05, sample_rate=SAMPLE_RATE)
        single_digit_len = int(SAMPLE_RATE * 0.5) + int(SAMPLE_RATE * 0.05)
        assert len(sequence) == single_digit_len * 3

    def test_invalid_characters_are_skipped(self):
        with_invalid = generate_dtmf_sequence("1#2", sample_rate=SAMPLE_RATE)
        without_invalid = generate_dtmf_sequence("12", sample_rate=SAMPLE_RATE)
        assert len(with_invalid) == len(without_invalid)

    def test_empty_string_yields_empty_sequence(self):
        sequence = generate_dtmf_sequence("")
        assert len(sequence) == 0

    def test_output_dtype_is_int16(self):
        sequence = generate_dtmf_sequence("7004191", sample_rate=SAMPLE_RATE)
        assert sequence.dtype == np.int16


class TestSaveWav:
    def test_writes_readable_wav_file(self, tmp_path):
        samples = generate_dtmf_sequence("5", sample_rate=SAMPLE_RATE)
        output_path = tmp_path / "test.wav"

        save_wav(samples, str(output_path), sample_rate=SAMPLE_RATE)

        assert output_path.exists()
        from scipy.io import wavfile

        read_rate, read_samples = wavfile.read(str(output_path))
        assert read_rate == SAMPLE_RATE
        assert np.array_equal(read_samples, samples)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
