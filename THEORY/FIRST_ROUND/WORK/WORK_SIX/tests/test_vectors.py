import numpy as np
import pytest

from wavelet_lab.vectors import (
    TOTAL_OUTPUT_LENGTH,
    VECTORS,
    _split_counts,
    correlation_vector_100,
    sliding_correlation,
)


def test_vector_shapes():
    assert VECTORS["Vector1"].size == 10
    assert VECTORS["Vector2"].size == 10
    assert VECTORS["Vector3"].size == 10
    assert VECTORS["Vector4"].size == 10
    assert VECTORS["Vector5"].size == 10
    assert VECTORS["Vector6"].size == 20


def test_vector_values():
    np.testing.assert_array_equal(VECTORS["Vector1"], np.ones(10))
    np.testing.assert_array_equal(VECTORS["Vector2"], np.zeros(10))
    np.testing.assert_array_equal(VECTORS["Vector3"], [1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(VECTORS["Vector4"], [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])


def test_split_counts_sums_to_total_and_is_even():
    counts = _split_counts(100, 6)
    assert sum(counts) == 100
    assert counts == [17, 17, 17, 17, 16, 16]


def test_sliding_correlation_matches_worked_example():
    # Assignment's worked example: Vector1 (all ones) dotted with the first
    # 10 samples of a hand-computable synthetic "audio" array.
    signal = np.arange(1.0, 21.0)  # [1, 2, ..., 20]
    result = sliding_correlation(VECTORS["Vector1"], signal, n_values=1)
    assert result[0] == sum(range(1, 11))  # 1+2+...+10 = 55


def test_sliding_correlation_multiple_positions():
    signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    vector = np.array([1.0, 1.0])  # boxcar of length 2
    result = sliding_correlation(vector, signal, n_values=4)
    np.testing.assert_allclose(result, [3.0, 5.0, 7.0, 9.0])


def test_sliding_correlation_zero_vector_is_all_zero():
    signal = np.arange(1.0, 21.0)
    result = sliding_correlation(VECTORS["Vector2"], signal, n_values=5)
    np.testing.assert_allclose(result, np.zeros(5))


def test_sliding_correlation_rejects_short_signal():
    with pytest.raises(ValueError):
        sliding_correlation(VECTORS["Vector1"], np.ones(5), n_values=1)


def test_correlation_vector_100_length_and_first_block():
    # Deterministic synthetic signal, long enough for every vector's block.
    signal = np.arange(1.0, 201.0)
    output = correlation_vector_100(signal)
    assert output.size == TOTAL_OUTPUT_LENGTH

    # First value is Vector1's lag-0 dot product with the first 10 samples.
    assert output[0] == sum(range(1, 11))  # 55
    # Vector1's block has 17 entries (see _split_counts); its second value
    # is the lag-1 sliding dot product.
    assert output[1] == sum(range(2, 12))  # 2+3+...+11 = 65


def test_correlation_vector_100_rejects_short_signal():
    with pytest.raises(ValueError):
        correlation_vector_100(np.ones(10))
