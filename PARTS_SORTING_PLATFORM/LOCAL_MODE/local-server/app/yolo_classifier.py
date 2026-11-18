"""YOLO-based part classifier, using the weights trained in
../training/ (see ../training/README.md). Replaces
shared/spectrum_classifier.py as local-server's live classifier --
that module is still used by CLOUD_MODE's classification-service, but
this project settled on YOLO for local-mode instead.

Honesty rule (same discipline as spectrum_classifier.py): if the
configured weights file doesn't exist, classify() always returns the
documented stub response -- never a fabricated label.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from PIL import Image

NO_WEIGHTS_REASON = "no YOLO weights found at configured path"
NO_DETECTION_REASON = "no object detected above confidence threshold"


class YoloClassifier:
    def __init__(self, weights_path: str, confidence_threshold: float = 0.25) -> None:
        self.weights_path = Path(weights_path)
        self.confidence_threshold = confidence_threshold
        self._model: Optional["object"] = None
        if self.weights_path.exists():
            from ultralytics import YOLO  # heavy import, deferred until weights confirmed present

            self._model = YOLO(str(self.weights_path))

    @property
    def is_stub(self) -> bool:
        return self._model is None

    def classify(self, image_bytes: bytes) -> dict:
        if self.is_stub:
            return {
                "label": "unclassified",
                "confidence": None,
                "stub": True,
                "reason": NO_WEIGHTS_REASON,
                "features": None,
            }

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = self._model.predict(source=image, conf=self.confidence_threshold, verbose=False)
        result = results[0]
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return {
                "label": "unclassified",
                "confidence": None,
                "stub": False,
                "reason": NO_DETECTION_REASON,
                "features": None,
            }

        best_idx = boxes.conf.argmax().item()
        class_id = int(boxes.cls[best_idx].item())
        confidence = float(boxes.conf[best_idx].item())
        label = result.names.get(class_id, f"id_{class_id}")

        return {
            "label": label,
            "confidence": confidence,
            "stub": False,
            "reason": None,
            "features": None,
        }


def build_classifier(weights_path: str) -> YoloClassifier:
    return YoloClassifier(weights_path=weights_path)
