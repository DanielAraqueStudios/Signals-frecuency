"""Main window for the DTMF Dialer desktop application.

Layout (see readme.md for a diagram):
    Header
    ┌─────────────────────────┬─────────────────────────┐
    │ Input panel              │ Waveform preview panel   │
    │  - phone number entry    │  - live plot of the      │
    │  - advanced settings     │    generated tone         │
    │  - Generate / Play        │                          │
    │  - status / progress      │                          │
    │  - history list           │                          │
    └─────────────────────────┴─────────────────────────┘

UI logic only lives here — all signal synthesis, file I/O, and playback are
delegated to `dtmf_dialer` via the threaded wrappers in `gui.workers`, so this
class never blocks and never reimplements backend behavior.
"""

from __future__ import annotations

import os
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .theme import STYLESHEET
from .waveform_canvas import WaveformCanvas
from .workers import GenerateWorker, PlayWorker

# WORK_ONE/dtmf_dialer/gui/main_window.py -> up 3 levels to reach WORK_ONE/output
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "output")
SAMPLE_RATE_OPTIONS = [8000, 16000, 22050, 44100, 48000]


class MainWindow(QMainWindow):
    """Top-level window: number entry, settings, waveform preview, and history."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DTMF Dialer")
        self.resize(880, 520)
        self.setMinimumSize(720, 460)

        self._generate_worker: GenerateWorker | None = None
        self._play_worker: PlayWorker | None = None
        self._current_output_path: str | None = None
        self._current_sample_rate: int = 44100
        self._playback_started_at: float = 0.0

        # Drives the real-time playhead: ticks at ~30 fps while audio plays,
        # reading elapsed wall-clock time since winsound gives no sample-
        # accurate playback position to poll.
        self._playhead_timer = QTimer(self)
        self._playhead_timer.setInterval(33)
        self._playhead_timer.timeout.connect(self._on_playhead_tick)

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(10)

        root_layout.addWidget(self._build_header())

        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)
        body_layout.addWidget(self._build_input_panel(), stretch=5)
        body_layout.addWidget(self._build_preview_panel(), stretch=4)
        root_layout.addLayout(body_layout, stretch=1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("DTMF Dial Tone Generator")
        title.setObjectName("HeaderLabel")
        subtitle = QLabel(
            "Enter a phone number to synthesize, preview, and play its DTMF dial tones."
        )
        subtitle.setObjectName("SubHeaderLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _build_input_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # --- Phone number input (the primary, always-visible control) ---
        number_label = QLabel("PHONE NUMBER")
        number_label.setObjectName("SectionTitle")
        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("e.g. 7004191")
        self.number_input.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[0-9]{0,20}"))
        )
        self.number_input.setToolTip("Digits 0-9 only. Other characters are rejected.")
        self.number_input.returnPressed.connect(self._on_generate_clicked)

        layout.addWidget(number_label)
        layout.addWidget(self.number_input)

        # --- Advanced settings (collapsible) ---
        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setObjectName("AdvancedToggle")
        self.advanced_toggle.setText("▸  Advanced settings")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.advanced_toggle.toggled.connect(self._on_advanced_toggled)
        layout.addWidget(self.advanced_toggle)

        self.advanced_panel = self._build_advanced_settings()
        self.advanced_panel.setVisible(False)
        layout.addWidget(self.advanced_panel)

        # --- Primary actions ---
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.generate_button = QPushButton("Generate")
        self.generate_button.setObjectName("GenerateButton")
        self.generate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_button.clicked.connect(self._on_generate_clicked)

        self.play_button = QPushButton("▶  Play")
        self.play_button.setObjectName("PlayButton")
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self._on_play_clicked)

        actions_layout.addWidget(self.generate_button, stretch=1)
        actions_layout.addWidget(self.play_button, stretch=1)
        layout.addLayout(actions_layout)

        # --- Feedback: progress bar + status label ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Enter a number and click Generate.")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setProperty("state", "idle")
        layout.addWidget(self.status_label)

        # --- History ---
        history_label = QLabel("HISTORY")
        history_label.setObjectName("SectionTitle")
        layout.addWidget(history_label)

        self.history_list = QListWidget()
        self.history_list.setToolTip("Double-click an entry to play it again.")
        self.history_list.itemDoubleClicked.connect(self._on_history_item_activated)
        layout.addWidget(self.history_list, stretch=1)

        return panel

    def _build_advanced_settings(self) -> QWidget:
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # Tone duration
        tone_row = QHBoxLayout()
        tone_row.addWidget(QLabel("Tone duration (s)"))
        self.tone_duration_input = QDoubleSpinBox()
        self.tone_duration_input.setRange(0.05, 2.0)
        self.tone_duration_input.setSingleStep(0.05)
        self.tone_duration_input.setValue(0.5)
        self.tone_duration_input.setToolTip("Length of each DTMF tone in seconds.")
        tone_row.addStretch(1)
        tone_row.addWidget(self.tone_duration_input)
        layout.addLayout(tone_row)

        # Pause duration
        pause_row = QHBoxLayout()
        pause_row.addWidget(QLabel("Pause between tones (s)"))
        self.pause_duration_input = QDoubleSpinBox()
        self.pause_duration_input.setRange(0.0, 1.0)
        self.pause_duration_input.setSingleStep(0.05)
        self.pause_duration_input.setValue(0.05)
        self.pause_duration_input.setToolTip("Silence inserted between consecutive tones.")
        pause_row.addStretch(1)
        pause_row.addWidget(self.pause_duration_input)
        layout.addLayout(pause_row)

        # Sample rate
        rate_row = QHBoxLayout()
        rate_row.addWidget(QLabel("Sample rate (Hz)"))
        self.sample_rate_input = QComboBox()
        self.sample_rate_input.addItems(str(rate) for rate in SAMPLE_RATE_OPTIONS)
        self.sample_rate_input.setCurrentText("44100")
        self.sample_rate_input.setToolTip("Audio sample rate used for synthesis and WAV export.")
        rate_row.addStretch(1)
        rate_row.addWidget(self.sample_rate_input)
        layout.addLayout(rate_row)

        return container

    def _build_preview_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("WAVEFORM PREVIEW")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.waveform_canvas = WaveformCanvas(panel)
        layout.addWidget(self.waveform_canvas, stretch=1)

        hint = QLabel("The green line tracks playback position in real time.")
        hint.setObjectName("SubHeaderLabel")
        layout.addWidget(hint)

        return panel

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def _on_advanced_toggled(self, checked: bool) -> None:
        self.advanced_panel.setVisible(checked)
        self.advanced_toggle.setText(("▾" if checked else "▸") + "  Advanced settings")

    def _on_generate_clicked(self) -> None:
        digits = self.number_input.text().strip()
        if not digits:
            self._set_status("Please enter a phone number first.", "error")
            return

        sample_rate = int(self.sample_rate_input.currentText())
        self._current_sample_rate = sample_rate
        output_path = os.path.join(OUTPUT_DIR, f"dial_{digits}.wav")

        self._set_busy(True, "Generating tone…")
        self._generate_worker = GenerateWorker(
            digits=digits,
            output_path=output_path,
            tone_duration_s=self.tone_duration_input.value(),
            pause_duration_s=self.pause_duration_input.value(),
            sample_rate=sample_rate,
        )
        self._generate_worker.succeeded.connect(self._on_generate_succeeded)
        self._generate_worker.failed.connect(self._on_generate_failed)
        self._generate_worker.finished.connect(lambda: self._set_busy(False))
        self._generate_worker.start()

    def _on_generate_succeeded(self, samples, output_path: str) -> None:
        self._current_output_path = output_path
        self.waveform_canvas.plot_samples(samples, self._current_sample_rate)
        self.play_button.setEnabled(True)
        self._set_status(f"Generated {os.path.basename(output_path)}", "success")
        self._add_history_entry(self.number_input.text().strip(), output_path)

    def _on_generate_failed(self, message: str) -> None:
        self._set_status(message, "error")

    def _on_play_clicked(self) -> None:
        if not self._current_output_path:
            return
        self._set_busy(True, "Playing…", disable_generate=False)
        self.play_button.setEnabled(False)
        self._play_worker = PlayWorker(self._current_output_path)
        self._play_worker.succeeded.connect(self._on_play_succeeded)
        self._play_worker.failed.connect(self._on_play_failed)
        self._play_worker.finished.connect(self._on_play_finished)

        # Start the real-time playhead animation in lockstep with playback.
        self._playback_started_at = time.monotonic()
        self._playhead_timer.start()
        self._play_worker.start()

    def _on_play_succeeded(self) -> None:
        self._set_status("Playback finished.", "success")

    def _on_play_failed(self, message: str) -> None:
        self._set_status(message, "error")

    def _on_play_finished(self) -> None:
        self._playhead_timer.stop()
        self.waveform_canvas.hide_playhead()
        self.progress_bar.setVisible(False)
        self.play_button.setEnabled(True)

    def _on_playhead_tick(self) -> None:
        elapsed_s = time.monotonic() - self._playback_started_at
        self.waveform_canvas.set_playhead(elapsed_s)
        if elapsed_s >= self.waveform_canvas.duration_s:
            self._playhead_timer.stop()

    def _on_history_item_activated(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path or not os.path.exists(path):
            self._set_status("That audio file is no longer available.", "error")
            return
        self._current_output_path = path
        self.play_button.setEnabled(True)
        self._reload_waveform(path)
        self._on_play_clicked()

    def _reload_waveform(self, path: str) -> None:
        """Re-plot a history entry's waveform by reading its WAV file back."""
        try:
            from scipy.io import wavfile

            sample_rate, samples = wavfile.read(path)
            self._current_sample_rate = sample_rate
            self.waveform_canvas.plot_samples(samples, sample_rate)
        except (OSError, ValueError) as exc:
            self._set_status(f"Could not preview that file: {exc}", "error")

    # ------------------------------------------------------------------ #
    # Feedback helpers
    # ------------------------------------------------------------------ #
    def _set_busy(self, busy: bool, message: str = "", disable_generate: bool = True) -> None:
        self.progress_bar.setVisible(busy)
        if disable_generate:
            self.generate_button.setEnabled(not busy)
        self.number_input.setEnabled(not busy)
        if busy:
            self._set_status(message, "loading")

    def _set_status(self, message: str, state: str) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _add_history_entry(self, digits: str, path: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"{digits}   ·   {timestamp}")
        item.setData(Qt.ItemDataRole.UserRole, path)
        self.history_list.insertItem(0, item)
