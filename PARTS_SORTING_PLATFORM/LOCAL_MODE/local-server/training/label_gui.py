"""PyQt6 GUI to load part photos, assign a class, and automatically write
them (plus their YOLO label .txt) into dataset/images/{train,val} and
dataset/labels/{train,val}.

Label mode: whole-image box (see GPU_SETUP.md's sibling README.md "Why a
full-frame box" note below). Each photo on this rig has a single centered
part, so instead of asking the user to draw a precise rectangle per photo,
the saved label covers almost the entire frame (a small margin is left so
the box isn't literally touching the image edges, which some YOLO augmentations
handle poorly). If parts end up off-center or multiple-per-photo in practice,
this assumption breaks and a manual bounding-box tool would be needed instead
-- not built here, out of scope for this GUI.

Usage:
    python label_gui.py
(or via ../../scripts/run_labeling_gui.py)

Requires requirements-gui.txt installed separately (PyQt6, Pillow) --
NOT part of requirements-training.txt or the server's requirements.txt.
"""
from __future__ import annotations

import random
import shutil
import sys
from pathlib import Path

import yaml
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

THIS_DIR = Path(__file__).resolve().parent
DATASET_DIR = THIS_DIR / "dataset"
DATA_YAML = THIS_DIR / "data.yaml"

# Fraction of images (per class) sent to val/ instead of train/. Simple
# random split per saved image -- not a guaranteed exact ratio, just an
# expected one over many images (see README.md's "85/15 split" guidance).
VAL_SPLIT_PROBABILITY = 0.15

# Margin left around the "whole image" box so it doesn't touch the frame
# edges exactly (normalized 0-1 units). See module docstring.
BOX_MARGIN = 0.03

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def load_class_names() -> list[str]:
    with open(DATA_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = data.get("names", {})
    # data.yaml stores names as {0: "brocas", 1: "escariadores", ...}
    return [names[i] for i in sorted(names.keys())]


def save_class_names(class_names: list[str]) -> None:
    """Rewrites data.yaml's `names` mapping, keeping path/train/val as-is.
    New classes are only ever appended (never reordered/removed here), so
    existing label .txt files -- which reference class ids by position --
    stay valid after this runs."""
    with open(DATA_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["names"] = {i: name for i, name in enumerate(class_names)}
    with open(DATA_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def whole_image_label_line(class_id: int) -> str:
    cx, cy = 0.5, 0.5
    w = 1.0 - 2 * BOX_MARGIN
    h = 1.0 - 2 * BOX_MARGIN
    return f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n"


def pick_split() -> str:
    return "val" if random.random() < VAL_SPLIT_PROBABILITY else "train"


class LabelGui(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Parts Sorting - Etiquetador de imágenes")
        self.resize(640, 520)

        self.class_names = load_class_names()
        self.pending_images: list[Path] = []
        self.current_index = 0
        self.saved_count = 0

        self._build_ui()
        self._show_current_image()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.status_label = QLabel("Ninguna imagen cargada todavía.")
        layout.addWidget(self.status_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(360)
        self.image_label.setStyleSheet("background-color: #222; color: white;")
        layout.addWidget(self.image_label)

        load_button = QPushButton("Cargar imágenes...")
        load_button.clicked.connect(self._on_load_images)
        layout.addWidget(load_button)

        self.apply_to_all_checkbox = QCheckBox(
            "Aplicar esta clase a TODAS las imágenes restantes (para lotes de la misma pieza)"
        )
        layout.addWidget(self.apply_to_all_checkbox)

        self.class_row = QHBoxLayout()
        for class_id, class_name in enumerate(self.class_names):
            self._add_class_button(class_id, class_name)
        layout.addLayout(self.class_row)

        bottom_row = QHBoxLayout()
        add_category_button = QPushButton("+ Agregar categoría")
        add_category_button.clicked.connect(self._on_add_category)
        bottom_row.addWidget(add_category_button)

        skip_button = QPushButton("Omitir esta imagen")
        skip_button.clicked.connect(self._on_skip)
        bottom_row.addWidget(skip_button)
        layout.addLayout(bottom_row)

    def _add_class_button(self, class_id: int, class_name: str) -> None:
        btn = QPushButton(class_name)
        btn.clicked.connect(lambda _checked, cid=class_id: self._on_assign_class(cid))
        self.class_row.addWidget(btn)

    def _on_add_category(self) -> None:
        name, ok = QInputDialog.getText(self, "Nueva categoría", "Nombre de la nueva categoría (sin espacios):")
        if not ok:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Nombre inválido", "El nombre no puede estar vacío.")
            return
        if any(existing.lower() == name.lower() for existing in self.class_names):
            QMessageBox.warning(self, "Categoría duplicada", f"'{name}' ya existe.")
            return

        new_class_id = len(self.class_names)
        self.class_names.append(name)
        try:
            save_class_names(self.class_names)
        except OSError as exc:
            self.class_names.pop()
            QMessageBox.warning(self, "Error al guardar", f"No se pudo actualizar data.yaml: {exc}")
            return
        self._add_class_button(new_class_id, name)

    def _show_current_image(self) -> None:
        if self.current_index >= len(self.pending_images):
            if self.pending_images:
                self.status_label.setText(
                    f"Listo. {self.saved_count} imagen(es) guardada(s) en esta sesión."
                )
            self.image_label.setText("Sin imagen")
            self.image_label.setPixmap(QPixmap())
            return

        path = self.pending_images[self.current_index]
        remaining = len(self.pending_images) - self.current_index
        self.status_label.setText(
            f"Imagen {self.current_index + 1}/{len(self.pending_images)} "
            f"({remaining} restante(s)) -- elige la clase: {path.name}"
        )
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                600, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText(f"No se pudo abrir: {path.name}")

    def _on_load_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecciona fotos de piezas",
            "",
            "Imágenes (*.jpg *.jpeg *.png *.bmp)",
        )
        if not files:
            return
        self.pending_images = [Path(f) for f in files if Path(f).suffix.lower() in SUPPORTED_EXTENSIONS]
        self.current_index = 0
        self._show_current_image()

    def _on_assign_class(self, class_id: int) -> None:
        if self.current_index >= len(self.pending_images):
            return

        if self.apply_to_all_checkbox.isChecked():
            self._assign_class_to_remaining(class_id)
            return

        src_path = self.pending_images[self.current_index]
        try:
            self._save_labeled_image(src_path, class_id)
            self.saved_count += 1
        except OSError as exc:
            QMessageBox.warning(self, "Error al guardar", f"No se pudo guardar {src_path.name}: {exc}")
        self.current_index += 1
        self._show_current_image()

    def _assign_class_to_remaining(self, class_id: int) -> None:
        """Saves every image from current_index to the end under class_id in
        one go -- for a batch of photos that are all the same part (e.g. 50
        photos taken in a row of only tornillos)."""
        failed: list[str] = []
        while self.current_index < len(self.pending_images):
            src_path = self.pending_images[self.current_index]
            try:
                self._save_labeled_image(src_path, class_id)
                self.saved_count += 1
            except OSError as exc:
                failed.append(f"{src_path.name}: {exc}")
            self.current_index += 1

        self.apply_to_all_checkbox.setChecked(False)
        if failed:
            QMessageBox.warning(
                self, "Algunas imágenes no se guardaron",
                "No se pudieron guardar:\n" + "\n".join(failed),
            )
        self._show_current_image()

    def _on_skip(self) -> None:
        if self.current_index >= len(self.pending_images):
            return
        self.current_index += 1
        self._show_current_image()

    def _save_labeled_image(self, src_path: Path, class_id: int) -> None:
        split = pick_split()
        images_dir = DATASET_DIR / "images" / split
        labels_dir = DATASET_DIR / "labels" / split
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        dest_image = self._unique_dest(images_dir, src_path.name)
        shutil.copy2(src_path, dest_image)

        label_path = labels_dir / (dest_image.stem + ".txt")
        label_path.write_text(whole_image_label_line(class_id), encoding="utf-8")

    @staticmethod
    def _unique_dest(directory: Path, filename: str) -> Path:
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


def main() -> int:
    app = QApplication(sys.argv)
    window = LabelGui()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
