"""Load a train.py checkpoint (.pt), export it to ONNX, then INT8-quantize
it dynamically -- producing model/weights/model.onnx, the file app/infer.py
checks for at startup to leave stub mode.

Requires the TRAINING environment (see model/README.md):
    pip install torch==2.4.1 torchvision==0.19.1 onnx==1.16.2

Usage:
    python export_onnx.py --checkpoint model/checkpoint.pt --out model/weights/model.onnx
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models


def load_model(checkpoint_path: str) -> tuple:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    classes = checkpoint["classes"]
    input_size = checkpoint.get("input_size", 224)

    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.last_channel, len(classes))
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, classes, input_size


def export(checkpoint_path: str, out_path: str) -> None:
    model, classes, input_size = load_model(checkpoint_path)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fp32_path = out.with_name(out.stem + "_fp32.onnx")

    dummy_input = torch.randn(1, 3, input_size, input_size)
    torch.onnx.export(
        model,
        dummy_input,
        str(fp32_path),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"Exported FP32 ONNX model to {fp32_path}")

    # "Most powerful configuration" here means the largest Railway CPU/RAM
    # plan (no GPU tier on Railway) running an INT8-quantized ONNX Runtime
    # model -- quantize_dynamic is what actually produces that INT8 model.
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(
        model_input=str(fp32_path),
        model_output=str(out),
        weight_type=QuantType.QInt8,
    )
    print(f"Quantized to INT8 and wrote {out}")
    print(f"Classes ({len(classes)}): {classes}")
    print("Confirm model/labels.json matches this class list/order before deploying.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", default="model/checkpoint.pt")
    parser.add_argument("--out", default="model/weights/model.onnx")
    args = parser.parse_args()
    export(args.checkpoint, args.out)


if __name__ == "__main__":
    main()
