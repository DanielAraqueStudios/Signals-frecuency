"""Synthetic-image tests for app/diameter_measurement.py -- draws a known
black marker line (1cm) and a known gray "part" circle on a white
background with OpenCV/numpy directly, so ground-truth diameter_cm is
known exactly, no real camera/photo needed."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from app.diameter_measurement import measure_diameter_cm


def _encode_png(image: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", image)
    assert ok
    return buf.tobytes()


def _synthetic_frame(marker_length_px: int, part_diameter_px: int) -> np.ndarray:
    image = np.full((300, 300, 3), 255, dtype=np.uint8)

    # Reference marker: thin black horizontal line, known pixel length.
    marker_y = 20
    cv2.line(image, (20, marker_y), (20 + marker_length_px, marker_y), (0, 0, 0), thickness=4)

    # Part: solid gray circle, known pixel diameter, well clear of the marker.
    center = (150, 180)
    radius = part_diameter_px // 2
    cv2.circle(image, center, radius, (128, 128, 128), thickness=-1)

    return image


def test_measures_diameter_within_tolerance_of_known_ground_truth():
    marker_length_px = 100  # defined as 1cm -> pixels_per_cm == 100
    part_diameter_px = 60  # expected diameter_cm == 0.6
    frame = _synthetic_frame(marker_length_px, part_diameter_px)

    result = measure_diameter_cm(_encode_png(frame))

    assert result["reason"] is None
    assert result["marker_segments_found"] >= 1
    assert result["pixels_per_cm"] == pytest.approx(marker_length_px, rel=0.1)
    expected_cm = part_diameter_px / marker_length_px
    assert result["diameter_cm"] == pytest.approx(expected_cm, rel=0.15)


def test_no_marker_present_returns_documented_failure():
    image = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.circle(image, (50, 50), 20, (128, 128, 128), thickness=-1)

    result = measure_diameter_cm(_encode_png(image))

    assert result["diameter_cm"] is None
    assert result["pixels_per_cm"] is None
    assert "marker" in result["reason"]


def test_marker_but_no_part_returns_documented_failure():
    image = np.full((100, 100, 3), 255, dtype=np.uint8)
    cv2.line(image, (10, 10), (90, 10), (0, 0, 0), thickness=4)

    result = measure_diameter_cm(_encode_png(image))

    assert result["diameter_cm"] is None
    assert result["marker_segments_found"] >= 1
    assert "part" in result["reason"]


def test_garbage_bytes_never_raises_and_returns_failure_reason():
    result = measure_diameter_cm(b"not an image")

    assert result["diameter_cm"] is None
    assert result["reason"] is not None
