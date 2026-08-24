"""Background QThread workers wrapping the dtmf_dialer backend.

Both worker classes exist so that no backend call — synthesis/file I/O in
`GenerateWorker`, or the blocking `winsound` call in `PlayWorker` — ever runs
on the Qt UI thread. Each emits `succeeded`/`failed` signals so the main
window can react (update UI, show errors) without polling or blocking.
"""

from __future__ import annotations

import os

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from dtmf_dialer import generate_dtmf_sequence, play_wav, save_wav


class GenerateWorker(QThread):
    """Synthesizes a DTMF sequence and writes it to disk off the UI thread.

    Emits:
        succeeded(np.ndarray, str): PCM samples and the output file path.
        failed(str): User-friendly error message.
    """

    succeeded = pyqtSignal(object, str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        digits: str,
        output_path: str,
        tone_duration_s: float,
        pause_duration_s: float,
        sample_rate: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._digits = digits
        self._output_path = output_path
        self._tone_duration_s = tone_duration_s
        self._pause_duration_s = pause_duration_s
        self._sample_rate = sample_rate

    def run(self) -> None:  # noqa: D102 (QThread override)
        try:
            samples: np.ndarray = generate_dtmf_sequence(
                self._digits,
                tone_duration_s=self._tone_duration_s,
                pause_duration_s=self._pause_duration_s,
                sample_rate=self._sample_rate,
            )
            if samples.size == 0:
                self.failed.emit(
                    "No valid digits found. Please enter digits 0-9 only."
                )
                return

            os.makedirs(os.path.dirname(self._output_path), exist_ok=True)
            save_wav(samples, self._output_path, sample_rate=self._sample_rate)
            self.succeeded.emit(samples, self._output_path)
        except OSError as exc:
            self.failed.emit(f"Could not write audio file: {exc.strerror or exc}")
        except Exception as exc:  # noqa: BLE001 - surface any unexpected failure safely
            self.failed.emit(f"Tone generation failed: {exc}")


class PlayWorker(QThread):
    """Plays a `.wav` file off the UI thread (winsound.PlaySound blocks).

    Emits:
        succeeded(): Playback finished normally.
        failed(str): User-friendly error message.
    """

    succeeded = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, path: str, parent=None) -> None:
        super().__init__(parent)
        self._path = path

    def run(self) -> None:  # noqa: D102 (QThread override)
        try:
            if not os.path.exists(self._path):
                self.failed.emit("Audio file no longer exists on disk.")
                return
            play_wav(self._path)
            self.succeeded.emit()
        except RuntimeError as exc:
            self.failed.emit(f"Playback failed: {exc}")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Playback failed: {exc}")
