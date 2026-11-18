"""PyQt6 GUI to try the trained YOLO model on a single image you pick --
loads an image, runs inference, and shows the annotated result (boxes +
predicted class + confidence) right in the window. Just for eyeballing
whether the model identifies a part correctly; doesn't save anything to
the dataset.

Usage:
    python test_image_gui.py
(or via ../../scripts/run_test_image_gui.py)

Requires requirements-gui.txt (PyQt6, Pillow) AND requirements-training.txt
(ultralytics) installed.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

THIS_DIR = Path(__file__).resolve().parent
RUNS_DIR = THIS_DIR / "runs"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def find_weights() -> list[Path]:
    """All best.pt under runs/*/weights/, newest first."""
    if not RUNS_DIR.is_dir():
        return []
    weights = list(RUNS_DIR.glob("*/weights/best.pt"))
    weights.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return weights


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    image = image.convert("RGB")
    data = image.tobytes("raw", "RGB")
    qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimage)


class TestImageGui(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Parts Sorting - Probar modelo con una imagen")
        self.resize(700, 600)

        self.model = None
        self.loaded_weights_path: Path | None = None
        self.image_path: Path | None = None

        self._build_ui()
        self._refresh_weights_list()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        weights_row = QHBoxLayout()
        weights_row.addWidget(QLabel("Pesos (best.pt):"))
        self.weights_combo = QComboBox()
        weights_row.addWidget(self.weights_combo)
        browse_weights_button = QPushButton("Buscar...")
        browse_weights_button.clicked.connect(self._on_browse_weights)
        weights_row.addWidget(browse_weights_button)
        layout.addLayout(weights_row)

        self.status_label = QLabel("Elegi una imagen para probar.")
        layout.addWidget(self.status_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(420)
        self.image_label.setStyleSheet("background-color: #222; color: white;")
        layout.addWidget(self.image_label)

        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.result_label)

        load_button = QPushButton("Cargar imagen y probar...")
        load_button.clicked.connect(self._on_load_image)
        layout.addWidget(load_button)

    def _refresh_weights_list(self) -> None:
        self.weights_combo.clear()
        for path in find_weights():
            self.weights_combo.addItem(f"{path.parent.parent.name}/weights/best.pt", userData=str(path))
        if self.weights_combo.count() == 0:
            self.weights_combo.addItem("(ninguno encontrado en runs/)", userData=None)

    def _on_browse_weights(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecciona un archivo .pt", str(RUNS_DIR), "Pesos (*.pt)")
        if file_path:
            self.weights_combo.insertItem(0, file_path, userData=file_path)
            self.weights_combo.setCurrentIndex(0)

    def _ensure_model_loaded(self) -> bool:
        weights_path_str = self.weights_combo.currentData()
        if not weights_path_str:
            QMessageBox.warning(self, "Sin pesos", "No hay ningun archivo best.pt disponible. Entrena el modelo primero.")
            return False
        weights_path = Path(weights_path_str)

        if self.model is not None and self.loaded_weights_path == weights_path:
            return True

        self.status_label.setText(f"Cargando modelo: {weights_path}...")
        QApplication.processEvents()
        try:
            from ultralytics import YOLO
            self.model = YOLO(str(weights_path))
            self.loaded_weights_path = weights_path
        except Exception as exc:  # noqa: BLE001 -- surfaced to the user, not swallowed
            QMessageBox.critical(self, "Error al cargar el modelo", str(exc))
            self.model = None
            self.loaded_weights_path = None
            return False
        return True

    def _on_load_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecciona una imagen", "", "Imagenes (*.jpg *.jpeg *.png *.bmp)"
        )
        if not file_path:
            return
        image_path = Path(file_path)
        if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            QMessageBox.warning(self, "Formato no soportado", f"Extension no soportada: {image_path.suffix}")
            return

        if not self._ensure_model_loaded():
            return

        self.image_path = image_path
        self.status_label.setText(f"Prediciendo sobre: {image_path.name}...")
        QApplication.processEvents()
        self._run_prediction(image_path)

    def _run_prediction(self, image_path: Path) -> None:
        try:
            results = self.model.predict(source=str(image_path), conf=0.25, verbose=False)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error al predecir", str(exc))
            self.status_label.setText("Error al predecir.")
            return

        result = results[0]
        annotated_bgr = result.plot()  # numpy array, BGR
        annotated_rgb = annotated_bgr[:, :, ::-1]
        annotated_image = Image.fromarray(annotated_rgb)

        pixmap = pil_to_qpixmap(annotated_image)
        pixmap = pixmap.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)

        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            self.result_label.setText("No se detecto ninguna clase (por debajo del umbral de confianza).")
            self.status_label.setText(f"Listo: {image_path.name}")
            return

        best_idx = boxes.conf.argmax().item()
        class_id = int(boxes.cls[best_idx].item())
        confidence = float(boxes.conf[best_idx].item())
        class_name = result.names.get(class_id, f"id_{class_id}")

        self.result_label.setText(f"Prediccion: {class_name} ({confidence * 100:.1f}%)")
        self.status_label.setText(f"Listo: {image_path.name}")


def main() -> int:
    app = QApplication(sys.argv)
    window = TestImageGui()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
