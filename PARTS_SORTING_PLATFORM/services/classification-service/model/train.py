"""Transfer-learning training script: MobileNetV2 (ImageNet-pretrained)
with a replaced classifier head, fine-tuned on data/<class_name>/*.jpg.

Requires the TRAINING environment, not the slim serving requirements.txt:
    pip install torch==2.4.1 torchvision==0.19.1

This was NOT run end-to-end in the environment this was written in (no
labeled dataset exists yet, and torch may not be installed there -- see
../README.md and the top-level model/README.md for the honest status).
It is correct, runnable Python that will work once both are available.

Usage:
    python train.py --data-dir data --epochs 10 --out model/checkpoint.pt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms


def build_transforms(input_size: int) -> tuple:
    # Matches app/infer.py's preprocessing exactly (resize + ImageNet
    # normalization) so the exported ONNX model sees the same distribution
    # of inputs at inference time that it was trained on.
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ]
    )
    val_tf = transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ]
    )
    return train_tf, val_tf


def train(data_dir: str, epochs: int, batch_size: int, lr: float, out_path: str, input_size: int) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_tf, val_tf = build_transforms(input_size)

    # ImageFolder derives class labels alphabetically from the
    # data/<class_name>/ subfolder names -- this order MUST match
    # labels.json's "classes" list, which train.py writes out below so the
    # two never drift apart.
    full_dataset = datasets.ImageFolder(data_dir, transform=train_tf)
    classes = full_dataset.classes
    if len(classes) < 2:
        raise ValueError(
            f"Found {len(classes)} class subfolder(s) under {data_dir!r}; "
            "need at least 2 (e.g. data/bolt/, data/screw/, ...)."
        )

    val_size = max(1, int(0.2 * len(full_dataset)))
    train_size = len(full_dataset) - val_size
    train_subset, val_subset = random_split(full_dataset, [train_size, val_size])
    # random_split shares train_tf via full_dataset; swap the val subset's
    # underlying transform so validation isn't augmented.
    val_dataset_view = datasets.ImageFolder(data_dir, transform=val_tf)
    val_subset.dataset = val_dataset_view

    train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_subset, batch_size=batch_size, shuffle=False, num_workers=2)

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, len(classes))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                preds = outputs.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        train_loss = running_loss / max(1, train_size)
        val_acc = correct / max(1, total)
        print(f"epoch {epoch + 1}/{epochs}  train_loss={train_loss:.4f}  val_acc={val_acc:.4f}")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "classes": classes, "input_size": input_size}, out_path)
    print(f"Saved checkpoint to {out_path}")

    labels_path = Path(__file__).parent / "labels.json"
    labels_path.write_text(
        json.dumps({"classes": classes, "input_size": input_size}, indent=2), encoding="utf-8"
    )
    print(f"Updated {labels_path} with the real class list from {data_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", help="expects data/<class_name>/*.jpg")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--input-size", type=int, default=224)
    parser.add_argument("--out", default="model/checkpoint.pt")
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.batch_size, args.lr, args.out, args.input_size)


if __name__ == "__main__":
    main()
