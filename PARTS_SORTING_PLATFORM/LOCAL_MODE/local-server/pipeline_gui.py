"""PyQt6 GUI to launch local-server with a chosen set of YOLO weights and
watch its logs live, in one window -- no separate terminal needed. Same
"select weights" pattern as test_image_gui.py, but instead of running
one-off inference, it starts the actual server subprocess (uvicorn) and
streams its stdout/stderr (band pause/resume, photo received,
classification results -- see app/main.py's logger.info() calls).

Usage:
    python pipeline_gui.py
(or via ../scripts/run_pipeline_gui.py)

Requires requirements-gui.txt (PyQt6) installed, same as the other GUIs
in this project.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QProcessEnvironment, Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

THIS_DIR = Path(__file__).resolve().parent
RUNS_DIR = THIS_DIR / "runs"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = "8100"

# Dark theme, same spirit as the other GUIs in this project but a little
# more deliberate: card-style sections, accent colors per log category
# instead of one flat green-on-black terminal look.
STYLESHEET = """
QMainWindow, QWidget { background-color: #1a1d23; color: #e6e6e6; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QLabel#title { font-size: 18px; font-weight: 600; color: #ffffff; }
QFrame#card { background-color: #22262e; border-radius: 10px; }
QComboBox, QPlainTextEdit { background-color: #0f1115; color: #e6e6e6; border: 1px solid #3a3f4a; border-radius: 6px; padding: 4px; }
QPushButton { border-radius: 6px; padding: 8px 16px; font-weight: 600; border: none; }
QPushButton#start { background-color: #2ecc71; color: #0a2412; }
QPushButton#start:disabled { background-color: #2a3a30; color: #5c6b63; }
QPushButton#stop { background-color: #e74c3c; color: #2a0b07; }
QPushButton#stop:disabled { background-color: #3a2a28; color: #6b5c5a; }
QPushButton#secondary { background-color: #3a3f4a; color: #e6e6e6; }
QPushButton#secondary:hover { background-color: #474d5a; }
"""

LOG_RULES: list[tuple[str, str]] = [
    (r"Band paused by|Pausa solicitada", "#f39c12"),
    (r"Band resumed by|Reanudado", "#2ecc71"),
    (r"Photo received", "#3498db"),
    (r"Classified sample_id", "#9b59b6"),
    (r"ERROR|error|Crashed|FAILED", "#e74c3c"),
    (r"Uvicorn running|startup complete", "#2ecc71"),
]
_LOG_PATTERNS = [(re.compile(pattern), color) for pattern, color in LOG_RULES]


def find_weights() -> list[Path]:
    """All best.pt under runs/*/weights/, newest first."""
    if not RUNS_DIR.is_dir():
        return []
    weights = list(RUNS_DIR.glob("*/weights/best.pt"))
    weights.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return weights


def colorize_line(line: str) -> str:
    escaped = html.escape(line)
    for pattern, color in _LOG_PATTERNS:
        if pattern.search(line):
            return f'<span style="color:{color};">{escaped}</span>'
    return f'<span style="color:#9aa0ab;">{escaped}</span>'


class PipelineGui(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Parts Sorting - Pipeline")
        self.resize(960, 640)
        self.setStyleSheet(STYLESHEET)

        self.process: QProcess | None = None
        self._pending_line = ""

        self._build_ui()
        self._refresh_weights_list()

        # Auto-start with the default (newest) weights as soon as the
        # window opens -- no need to click "Iniciar servidor" manually.
        if self.weights_combo.currentData():
            self._on_start()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        title = QLabel("Parts Sorting - Pipeline")
        title.setObjectName("title")
        outer.addWidget(title)

        control_card = QFrame()
        control_card.setObjectName("card")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(16, 14, 16, 14)
        control_layout.setSpacing(10)

        weights_row = QHBoxLayout()
        weights_row.addWidget(QLabel("Pesos (best.pt):"))
        self.weights_combo = QComboBox()
        weights_row.addWidget(self.weights_combo, stretch=1)
        browse_button = QPushButton("Buscar...")
        browse_button.setObjectName("secondary")
        browse_button.clicked.connect(self._on_browse_weights)
        weights_row.addWidget(browse_button)
        control_layout.addLayout(weights_row)

        buttons_row = QHBoxLayout()
        self.start_button = QPushButton("▶  Iniciar servidor")
        self.start_button.setObjectName("start")
        self.start_button.clicked.connect(self._on_start)
        buttons_row.addWidget(self.start_button)
        self.stop_button = QPushButton("■  Detener servidor")
        self.stop_button.setObjectName("stop")
        self.stop_button.clicked.connect(self._on_stop)
        self.stop_button.setEnabled(False)
        buttons_row.addWidget(self.stop_button)
        clear_log_button = QPushButton("Limpiar logs")
        clear_log_button.setObjectName("secondary")
        clear_log_button.clicked.connect(lambda: self.log_view.clear())
        buttons_row.addWidget(clear_log_button)
        buttons_row.addStretch(1)
        control_layout.addLayout(buttons_row)

        status_row = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #e74c3c; font-size: 16px;")
        status_row.addWidget(self.status_dot)
        self.status_label = QLabel("Detenido.")
        status_row.addWidget(self.status_label)
        status_row.addStretch(1)
        control_layout.addLayout(status_row)

        outer.addWidget(control_card)

        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(12, 12, 12, 12)
        log_label = QLabel("Logs en vivo")
        log_label.setStyleSheet("font-weight: 600; color: #aab0bb;")
        log_layout.addWidget(log_label)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        self.log_view.setStyleSheet(
            "background-color: #0b0d10; color: #d6d6d6; font-family: Consolas, 'Cascadia Mono', monospace; "
            "font-size: 12px; border: none;"
        )
        log_layout.addWidget(self.log_view)
        outer.addWidget(log_card, stretch=1)

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

    def _append_log(self, text: str) -> None:
        # Buffer partial lines across chunks so coloring rules match
        # whole lines, not arbitrary stdout fragments.
        self._pending_line += text
        lines = self._pending_line.split("\n")
        self._pending_line = lines[-1]
        for line in lines[:-1]:
            self.log_view.moveCursor(QTextCursor.MoveOperation.End)
            self.log_view.appendHtml(colorize_line(line))
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)

    def _set_status(self, text: str, color: str) -> None:
        self.status_label.setText(text)
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 16px;")

    def _on_start(self) -> None:
        weights_path_str = self.weights_combo.currentData()
        if not weights_path_str:
            QMessageBox.warning(self, "Sin pesos", "No hay ningun archivo best.pt seleccionado. Entrena el modelo primero o usa 'Buscar...'.")
            return

        weights_path = Path(weights_path_str)
        if not weights_path.exists():
            QMessageBox.warning(self, "Archivo no encontrado", f"No existe: {weights_path}")
            return

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.setWorkingDirectory(str(THIS_DIR))

        # QProcess.processEnvironment() returns an EMPTY environment by
        # default (it does NOT inherit the parent's) -- using that alone
        # would wipe out USERPROFILE/SystemRoot/etc. and break Python
        # itself (seen failing with "Could not determine home directory").
        # systemEnvironment() is the real inherited one to build on.
        env = QProcessEnvironment.systemEnvironment()
        # Overrides app/config.py's Settings.yolo_weights_path -- pydantic-settings
        # reads env vars case-insensitively by default, matching the field name.
        env.insert("YOLO_WEIGHTS_PATH", str(weights_path))
        self.process.setProcessEnvironment(env)

        self.process.readyReadStandardOutput.connect(self._on_process_output)
        self.process.finished.connect(self._on_process_finished)
        self.process.errorOccurred.connect(self._on_process_error)

        self._append_log(f"[pipeline_gui] Iniciando con pesos: {weights_path}\n")
        self.process.start(
            sys.executable,
            ["-m", "uvicorn", "app.main:app", "--host", DEFAULT_HOST, "--port", DEFAULT_PORT],
        )

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.weights_combo.setEnabled(False)
        self._set_status(f"Corriendo en http://{DEFAULT_HOST}:{DEFAULT_PORT} con {weights_path.name}", "#2ecc71")

    def _on_process_output(self) -> None:
        if self.process is None:
            return
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self._append_log(data)

    def _on_process_finished(self) -> None:
        self._append_log("\n[pipeline_gui] Servidor detenido.\n")
        self._set_status("Detenido.", "#e74c3c")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.weights_combo.setEnabled(True)
        self.process = None

    def _on_process_error(self, error) -> None:  # noqa: ANN001 -- QProcess.ProcessError enum
        self._append_log(f"\n[pipeline_gui] ERROR de proceso: {error}\n")

    def _on_stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()

    def closeEvent(self, event) -> None:  # noqa: ANN001 -- Qt override signature
        self._on_stop()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    window = PipelineGui()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
