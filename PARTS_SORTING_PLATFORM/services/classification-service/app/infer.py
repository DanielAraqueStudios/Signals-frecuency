"""ONNX Runtime inference wrapper, with an honest stub mode.

If model/weights/model.onnx is not present at startup, `infer()` always
returns the documented stub response -- never a fabricated label dressed
up as real. This mirrors the "pendiente" discipline used elsewhere in this
repo (see THEORY/ and LAB_TESTING/LAB1/) for results that haven't actually
been measured yet. Swap in a real model.onnx (see ../model/README.md) and
stub mode turns off automatically, purely by file presence -- no config
flag to remember to flip.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

STUB_REASON = "no trained model present"


class Classifier:
    def __init__(self, model_path: str, labels_path: str) -> None:
        self.model_path = model_path
        self.labels_path = labels_path
        self.session = None
        self.input_name: Optional[str] = None
        self.input_size = 224
        self.classes: list[str] = []

        self._load_labels()
        self._load_model_if_present()

    def _load_labels(self) -> None:
        path = Path(self.labels_path)
        if not path.exists():
            # No labels file at all -- stub mode regardless of model
            # presence, since we'd have nothing to name a prediction with.
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self.classes = list(data.get("classes", []))
        self.input_size = int(data.get("input_size", 224))

    def _load_model_if_present(self) -> None:
        if not Path(self.model_path).exists():
            return
        # Imported lazily so a missing/broken onnxruntime install can't
        # break stub-mode startup -- only matters once a model is present.
        import onnxruntime as ort

        self.session = ort.InferenceSession(
            self.model_path, providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name

    @property
    def is_stub(self) -> bool:
        return self.session is None or not self.classes

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        img = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGB")
        img = img.resize((self.input_size, self.input_size))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        # ImageNet normalization -- matches torchvision's pretrained
        # MobileNetV2 preprocessing used in model/train.py.
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = (arr - mean) / std
        arr = arr.transpose(2, 0, 1)  # HWC -> CHW
        return np.expand_dims(arr, axis=0)

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - np.max(logits)
        exp = np.exp(shifted)
        return exp / np.sum(exp)

    def infer(self, image_bytes: bytes) -> dict:
        if self.is_stub:
            return {"label": "unclassified", "confidence": None, "stub": True, "reason": STUB_REASON}

        input_tensor = self._preprocess(image_bytes)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        logits = outputs[0][0]
        probs = self._softmax(logits)
        top_idx = int(np.argmax(probs))
        return {
            "label": self.classes[top_idx],
            "confidence": float(probs[top_idx]),
            "stub": False,
            "reason": None,
        }


def build_classifier() -> Classifier:
    from app.config import settings

    return Classifier(model_path=settings.model_path, labels_path=settings.labels_path)
