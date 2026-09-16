"""Unit tests for services/shared/spectrum_classifier.py -- deterministic,
no ML/training fixtures needed: synthetic images with a known dominant
spatial frequency, checked against the extracted radial-band features."""

from __future__ import annotations

import io
import json

import numpy as np
import pytest
from PIL import Image

from shared.spectrum_classifier import (
    STUB_REASON,
    SpectrumClassifier,
    extract_features,
)


def _image_bytes(arr: np.ndarray) -> bytes:
    img = Image.fromarray(arr.astype("uint8"), mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _flat_image_bytes(size: int = 256, value: int = 128) -> bytes:
    """A uniform-gray image -- almost all spectral energy concentrated at
    DC (zero frequency), i.e. the lowest radial band."""
    return _image_bytes(np.full((size, size), value))


def _high_frequency_checkerboard_bytes(size: int = 256) -> bytes:
    """Alternating single-pixel checkerboard -- energy concentrated in the
    highest radial band (Nyquist-adjacent spatial frequency)."""
    yy, xx = np.mgrid[0:size, 0:size]
    pattern = ((yy + xx) % 2) * 255
    return _image_bytes(pattern)


def test_extract_features_returns_three_normalized_bands_summing_to_one():
    features = extract_features(_flat_image_bytes())
    assert len(features) == 3
    assert pytest.approx(sum(features), abs=1e-6) == 1.0


def test_flat_image_concentrates_energy_in_low_band():
    features = extract_features(_flat_image_bytes())
    low, mid, high = features
    assert low > mid
    assert low > high


def test_checkerboard_concentrates_energy_in_high_band_relative_to_flat_image():
    flat_low, _, _ = extract_features(_flat_image_bytes())
    checker_low, _, checker_high = extract_features(_high_frequency_checkerboard_bytes())
    assert checker_high > 0.0  # sanity: high band isn't ~0
    assert checker_low < flat_low  # far less low-band energy than a flat image


def test_classifier_is_stub_when_no_labels_config_present(tmp_path):
    classifier = SpectrumClassifier(labels_config_path=str(tmp_path / "missing.json"))

    assert classifier.is_stub is True
    result = classifier.classify(_flat_image_bytes())
    assert result == {
        "label": "unclassified",
        "confidence": None,
        "stub": True,
        "reason": STUB_REASON,
        "features": None,
    }


def test_classifier_matches_nearest_reference_profile(tmp_path):
    config_path = tmp_path / "labels_config.json"
    flat_features = extract_features(_flat_image_bytes())
    checker_features = extract_features(_high_frequency_checkerboard_bytes())
    config_path.write_text(
        json.dumps(
            {
                "classes": {
                    "smooth_part": {"reference_features": flat_features},
                    "textured_part": {"reference_features": checker_features},
                }
            }
        )
    )

    classifier = SpectrumClassifier(labels_config_path=str(config_path))
    assert classifier.is_stub is False

    result = classifier.classify(_flat_image_bytes())
    assert result["stub"] is False
    assert result["label"] == "smooth_part"
    assert result["confidence"] > 0.0
