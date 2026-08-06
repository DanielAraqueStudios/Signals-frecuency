"""Embedded Matplotlib canvas for previewing DTMF waveforms and animating
a real-time playhead synced to audio playback progress.
"""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# The full dial sequence can span several seconds at 44.1 kHz — too many
# points to render smoothly, so we cap the plotted point count and let
# `plot_samples` downsample (min/max envelope) to fit.
MAX_PLOT_POINTS = 4000

_BG_COLOR = "#1e1f26"
_LINE_COLOR = "#5b8cff"
_PLAYHEAD_COLOR = "#34d399"
_GRID_COLOR = "#33353f"
_TEXT_COLOR = "#9ca3af"


class WaveformCanvas(FigureCanvasQTAgg):
    """Dark-themed waveform plot with a real-time playback playhead."""

    def __init__(self, parent=None) -> None:
        figure = Figure(figsize=(4, 2), dpi=100, facecolor=_BG_COLOR)
        super().__init__(figure)
        self.setParent(parent)
        self._axes = figure.add_subplot(111)
        self._duration_s = 0.0
        self._playhead_line = None
        self._style_axes()

    def _style_axes(self) -> None:
        """Apply dark-theme styling to the plot axes."""
        axes = self._axes
        axes.set_facecolor(_BG_COLOR)
        axes.tick_params(colors=_TEXT_COLOR, labelsize=8)
        for spine in axes.spines.values():
            spine.set_color(_GRID_COLOR)
        axes.grid(True, color=_GRID_COLOR, linewidth=0.5)
        axes.set_xlabel("Time (s)", color=_TEXT_COLOR, fontsize=8)
        axes.set_ylabel("Amplitude", color=_TEXT_COLOR, fontsize=8)

    def plot_samples(self, samples: np.ndarray, sample_rate: int) -> None:
        """Render the full waveform (downsampled to stay responsive).

        Args:
            samples: int16 PCM samples for the whole generated sequence.
            sample_rate: Samples per second (Hz), used for the time axis.
        """
        self._duration_s = len(samples) / sample_rate if sample_rate else 0.0
        time_axis, plotted = self._downsample(samples, sample_rate)

        self._axes.clear()
        self._style_axes()
        self._axes.plot(time_axis, plotted, color=_LINE_COLOR, linewidth=0.8)
        self._axes.set_xlim(0, max(self._duration_s, 0.001))
        self._playhead_line = self._axes.axvline(0, color=_PLAYHEAD_COLOR, linewidth=1.5, visible=False)
        self.draw_idle()

    @staticmethod
    def _downsample(samples: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
        """Reduce sample count for plotting while preserving peak shape.

        Splits the signal into `MAX_PLOT_POINTS` chunks and keeps each
        chunk's max-magnitude sample, so tone envelopes stay visible even
        for multi-second sequences.
        """
        n = len(samples)
        if n <= MAX_PLOT_POINTS:
            time_axis = np.arange(n) / sample_rate
            return time_axis, samples

        chunk_size = n // MAX_PLOT_POINTS
        trimmed = samples[: chunk_size * MAX_PLOT_POINTS]
        chunks = trimmed.reshape(MAX_PLOT_POINTS, chunk_size)
        envelope = chunks[np.arange(MAX_PLOT_POINTS), np.argmax(np.abs(chunks), axis=1)]
        time_axis = (np.arange(MAX_PLOT_POINTS) * chunk_size) / sample_rate
        return time_axis, envelope

    def set_playhead(self, elapsed_s: float) -> None:
        """Move the playhead line to the given elapsed playback time.

        Args:
            elapsed_s: Seconds elapsed since playback started.
        """
        if self._playhead_line is None:
            return
        position = min(elapsed_s, self._duration_s)
        self._playhead_line.set_xdata([position, position])
        self._playhead_line.set_visible(True)
        self.draw_idle()

    def hide_playhead(self) -> None:
        """Hide the playhead line (e.g. when playback finishes or resets)."""
        if self._playhead_line is not None:
            self._playhead_line.set_visible(False)
            self.draw_idle()

    @property
    def duration_s(self) -> float:
        """Duration in seconds of the currently plotted sequence."""
        return self._duration_s

    def clear_plot(self) -> None:
        """Reset the canvas to an empty state."""
        self._axes.clear()
        self._style_axes()
        self._playhead_line = None
        self._duration_s = 0.0
        self.draw_idle()
