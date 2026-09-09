"""Stub-mode response shape, tested directly against app/infer.py --
no FastAPI/MQTT involved."""

from __future__ import annotations

from app.infer import Classifier


def test_stub_mode_when_no_model_file_present(tmp_path, sample_jpeg_bytes):
    labels_path = tmp_path / "labels.json"
    labels_path.write_text('{"classes": ["bolt", "screw"], "input_size": 224}')

    classifier = Classifier(model_path=str(tmp_path / "missing.onnx"), labels_path=str(labels_path))

    assert classifier.is_stub is True
    result = classifier.infer(sample_jpeg_bytes)
    assert result == {
        "label": "unclassified",
        "confidence": None,
        "stub": True,
        "reason": "no trained model present",
    }


def test_stub_mode_when_labels_file_missing_too(tmp_path, sample_jpeg_bytes):
    classifier = Classifier(
        model_path=str(tmp_path / "missing.onnx"), labels_path=str(tmp_path / "missing.json")
    )

    assert classifier.is_stub is True
    result = classifier.infer(sample_jpeg_bytes)
    assert result["stub"] is True
    assert result["label"] == "unclassified"
