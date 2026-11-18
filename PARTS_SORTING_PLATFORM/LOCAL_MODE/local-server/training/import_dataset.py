"""Bulk-import a folder of pre-sorted photos into dataset/images/{train,val}
and dataset/labels/{train,val}, using the same whole-image-box labeling rule
as label_gui.py.

Source layout expected: one subfolder per batch, named with a class prefix,
e.g. "Broca_1.0in/", "Escariador_2/". Everything inside a subfolder gets the
class implied by its prefix (case-insensitive, matched against data.yaml's
class names) -- the rest of the folder name (size/id) is not used as a label,
since the dataset only classifies part type, not diameter.

Usage:
    python import_dataset.py "C:\\path\\to\\Fotos Senales"
"""
from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path

import yaml

THIS_DIR = Path(__file__).resolve().parent
DATASET_DIR = THIS_DIR / "dataset"
DATA_YAML = THIS_DIR / "data.yaml"

VAL_SPLIT_PROBABILITY = 0.15
BOX_MARGIN = 0.03
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

# Folder-prefix -> class name. Checked in order, first match wins.
PREFIX_TO_CLASS = {
    "broca_centropunto": "broca_centropunto",
    "broca": "brocas",
    "escariador": "escariadores",
    "tornillo": "tornillos",
}


def load_class_names() -> list[str]:
    with open(DATA_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = data.get("names", {})
    return [names[i] for i in sorted(names.keys())]


def classify_folder_name(folder_name: str, class_names: list[str]) -> str | None:
    lowered = folder_name.lower()
    for prefix, class_name in PREFIX_TO_CLASS.items():
        if lowered.startswith(prefix) and class_name in class_names:
            return class_name
    return None


def whole_image_label_line(class_id: int) -> str:
    cx, cy = 0.5, 0.5
    w = 1.0 - 2 * BOX_MARGIN
    h = 1.0 - 2 * BOX_MARGIN
    return f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n"


def pick_split() -> str:
    return "val" if random.random() < VAL_SPLIT_PROBABILITY else "train"


def unique_dest(directory: Path, filename: str) -> Path:
    dest = directory / filename
    if not dest.exists():
        return dest
    stem, suffix = Path(filename).stem, Path(filename).suffix
    counter = 1
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def import_folder(src_root: Path) -> None:
    class_names = load_class_names()
    class_id_by_name = {name: i for i, name in enumerate(class_names)}

    counts: dict[str, int] = {}
    skipped: list[str] = []

    for subfolder in sorted(p for p in src_root.iterdir() if p.is_dir()):
        class_name = classify_folder_name(subfolder.name, class_names)
        if class_name is None:
            skipped.append(subfolder.name)
            continue
        class_id = class_id_by_name[class_name]

        for src_path in sorted(subfolder.iterdir()):
            if src_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            split = pick_split()
            images_dir = DATASET_DIR / "images" / split
            labels_dir = DATASET_DIR / "labels" / split
            images_dir.mkdir(parents=True, exist_ok=True)
            labels_dir.mkdir(parents=True, exist_ok=True)

            dest_image = unique_dest(images_dir, src_path.name)
            shutil.copy2(src_path, dest_image)

            label_path = labels_dir / (dest_image.stem + ".txt")
            label_path.write_text(whole_image_label_line(class_id), encoding="utf-8")

            counts[class_name] = counts.get(class_name, 0) + 1

    print("Imported:")
    for class_name, count in sorted(counts.items()):
        print(f"  {class_name}: {count}")
    if skipped:
        print("Skipped (no matching class prefix):")
        for name in skipped:
            print(f"  {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=str, help="Folder containing class-named subfolders of photos")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src_root = Path(args.source)
    if not src_root.is_dir():
        print(f"ERROR: not a folder: {src_root}")
        return 1
    import_folder(src_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
