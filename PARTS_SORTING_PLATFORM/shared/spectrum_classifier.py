"""Frequency-spectrum image classifier, shared by classification-service
(Railway) and local-server (local HTTP mode) -- see
../../docs/architecture.md for why both deployments use this same module
instead of an ML model.

Pipeline: grayscale -> 2D FFT (np.fft.fft2 + fftshift) -> magnitude
spectrum -> radial energy-band feature vector -> nearest-centroid match
against reference profiles in labels_config.json.

Honesty rule (same discipline as the rest of this repo -- see
THEORY/ and LAB_TESTING/LAB1/ for the same "pendiente" pattern): with no
labels_config.json (or an empty one), there are no reference profiles to
match against, so classify() always returns the documented stub response
-- never a fabricated label.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

STUB_REASON = "no reference spectrum profiles configured"

# Radial frequency bands, as fractions of the spectrum's max radius.
# (low, mid, high) energy split -- coarse but enough to distinguish
# part shapes with clearly different edge/texture density.
BAND_EDGES = (0.0, 0.15, 0.4, 1.0)


def _radial_band_energies(magnitude: np.ndarray) -> list[float]:
    h, w = magnitude.shape
    cy, cx = h / 2.0, w / 2.0
    yy, xx = np.mgrid[0:h, 0:w]
    radius = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    max_radius = radius.max() or 1.0
    normalized_radius = radius / max_radius

    energies = []
    total = magnitude.sum() or 1.0
    edges = list(zip(BAND_EDGES[:-1], BAND_EDGES[1:]))
    for i, (lo, hi) in enumerate(edges):
        if i == len(edges) - 1:
            band_mask = (normalized_radius >= lo) & (normalized_radius <= hi)
        else:
            band_mask = (normalized_radius >= lo) & (normalized_radius < hi)
        energies.append(float(magnitude[band_mask].sum() / total))
    return energies


def extract_features(image_bytes: bytes, resize_to: int = 256) -> list[float]:
    """Returns [low_band, mid_band, high_band] normalized energy fractions
    from the image's 2D FFT magnitude spectrum."""
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = img.resize((resize_to, resize_to))
    arr = np.asarray(img, dtype=np.float64)

    spectrum = np.fft.fftshift(np.fft.fft2(arr))
    magnitude = np.abs(spectrum)

    return _radial_band_energies(magnitude)


class SpectrumClassifier:
    def __init__(self, labels_config_path: str) -> None:
        self.labels_config_path = labels_config_path
        self.profiles: dict[str, list[float]] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        path = Path(self.labels_config_path)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        for class_name, profile in data.get("classes", {}).items():
            features = profile.get("reference_features")
            if features:
                self.profiles[class_name] = [float(v) for v in features]

    @property
    def is_stub(self) -> bool:
        return not self.profiles

    def classify(self, image_bytes: bytes) -> dict:
        if self.is_stub:
            return {
                "label": "unclassified",
                "confidence": None,
                "stub": True,
                "reason": STUB_REASON,
                "features": None,
            }

        features = extract_features(image_bytes)
        feature_vec = np.array(features)

        best_label: Optional[str] = None
        best_distance = float("inf")
        for label, reference in self.profiles.items():
            distance = float(np.linalg.norm(feature_vec - np.array(reference)))
            if distance < best_distance:
                best_distance = distance
                best_label = label

        # Convert distance to a rough [0, 1] confidence -- smaller distance
        # is better; this is a heuristic, not a calibrated probability.
        confidence = 1.0 / (1.0 + best_distance)

        return {
            "label": best_label,
            "confidence": confidence,
            "stub": False,
            "reason": None,
            "features": features,
        }


def build_classifier(labels_config_path: str) -> SpectrumClassifier:
    return SpectrumClassifier(labels_config_path=labels_config_path)
