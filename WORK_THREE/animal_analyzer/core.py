"""Audio loading, windowing, and statistical/spectral analysis (item 8).

GUI-free functions factored out of the analyzer app so they can be unit
tested and reused independently of `gui.py`. Implements the item 8 spec:
recordings are ~10 s long, but only the first 3 s are plotted and fed to
the FFT/mean/std analysis.
"""

from __future__ import annotations

import numpy as np

from signal_lab.spectral import compute_fft, dominant_frequency, signal_stats

# item 8: "los audios son de 10 segundos y se grafican solamente 3 segundos"
ANALYSIS_WINDOW_S = 3.0


def load_audio(path: str) -> tuple[np.ndarray, int]:
    """Load a mono audio file at its native sample rate.

    `librosa` is imported lazily here (rather than at module level) so
    the rest of this module — and everything that depends only on it,
    like `analyze_audio` — stays importable and testable without that
    (heavy, optional) dependency installed.

    Args:
        path: Path to a `.wav`/`.mp3`/`.flac`/`.ogg`/`.m4a` file.

    Returns:
        `(signal, sample_rate)`.
    """
    import librosa

    signal, sample_rate = librosa.load(path, sr=None, mono=True)
    return signal, sample_rate


def analysis_window(signal: np.ndarray, sample_rate: int, window_s: float = ANALYSIS_WINDOW_S) -> np.ndarray:
    """Truncate a signal to its first `window_s` seconds.

    Args:
        signal: Full audio signal.
        sample_rate: Samples per second (Hz).
        window_s: Length of the window to keep, in seconds.

    Returns:
        The first `window_s` seconds of `signal` (the whole signal if it
        is shorter than that).
    """
    n_samples = int(window_s * sample_rate)
    return signal[:n_samples]


def analyze_audio(signal: np.ndarray, sample_rate: int, window_s: float = ANALYSIS_WINDOW_S) -> dict:
    """Run the item-8 analysis on an audio signal: window, FFT, mean, std.

    Args:
        signal: Full audio signal, as returned by `load_audio`.
        sample_rate: Samples per second (Hz).
        window_s: Length of the analysis window, in seconds.

    Returns:
        Dict with `windowed_signal`, `sample_rate`, `frequencies`,
        `magnitude`, `dominant_frequency_hz`, `mean`, `std`.

    Raises:
        ValueError: If `signal` is empty.
    """
    windowed = analysis_window(signal, sample_rate, window_s)
    frequencies, magnitude = compute_fft(windowed, sample_rate)
    stats = signal_stats(windowed)
    return {
        "windowed_signal": windowed,
        "sample_rate": sample_rate,
        "frequencies": frequencies,
        "magnitude": magnitude,
        "dominant_frequency_hz": dominant_frequency(frequencies, magnitude),
        "mean": stats["mean"],
        "std": stats["std"],
    }


def separability_score(result_a: dict, result_b: dict) -> float:
    """Rough separability score between two `analyze_audio` results.

    Defined as the gap between their dominant frequencies divided by the
    sum of their standard deviations (a signal-processing analogue of a
    t-statistic): a large score means the two categories' dominant tones
    sit far apart relative to how "spread out"/noisy each signal is,
    which makes them easy to tell apart by ear or by a simple classifier;
    a small score means their spectra likely overlap.

    Args:
        result_a: Output of `analyze_audio` for category A.
        result_b: Output of `analyze_audio` for category B.

    Returns:
        A non-negative score; higher means more separable. `0.0` if both
        standard deviations are `0`.
    """
    freq_gap = abs(result_a["dominant_frequency_hz"] - result_b["dominant_frequency_hz"])
    spread = result_a["std"] + result_b["std"]
    if spread == 0:
        return 0.0
    return freq_gap / spread


def compare_categories(results: dict[str, dict]) -> str:
    """Build a plain-text separability report across analyzed categories.

    Args:
        results: Mapping of category name (e.g. "Gato") to its
            `analyze_audio` output.

    Returns:
        A human-readable summary: per-category mean/std/dominant
        frequency, then a pairwise separability score with a short
        qualitative note (heurstic threshold at score >= 3 = "clearly
        separable", >= 1 = "partially separable", else "likely overlapping").
    """
    lines = ["Resumen por categoría:"]
    for name, result in results.items():
        lines.append(
            f"  - {name}: media={result['mean']:.4f}, std={result['std']:.4f}, "
            f"frecuencia dominante={result['dominant_frequency_hz']:.1f} Hz"
        )

    names = list(results)
    lines.append("\nSeparabilidad estadística (pares):")
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            score = separability_score(results[a], results[b])
            if score >= 3:
                verdict = "claramente separables"
            elif score >= 1:
                verdict = "parcialmente separables"
            else:
                verdict = "espectros probablemente solapados"
            lines.append(f"  - {a} vs {b}: score={score:.2f} -> {verdict}")

    return "\n".join(lines)
