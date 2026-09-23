"""CLI entry point.

Item A: manually-derived 2nd-order Butterworth low-pass (bilinear
transform), applied via a for-loop difference equation, at cutoffs 40 Hz
and 100 Hz.

Item B: manually-derived 4th-order Butterworth (cascade of two biquads),
applied via the same for-loop, compared against `scipy.signal.butter` +
`scipy.signal.lfilter`.

Usage:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from filter_lab import (
    apply_cascade,
    apply_difference_equation,
    biquad_butterworth_bilinear,
    combine_sections,
    generate_test_signal,
    order4_manual_sections,
    scipy_butter_lowpass,
)
from filter_lab.plotting import plot_before_after_spectrum, plot_manual_vs_scipy
from filter_lab.signals import DEFAULT_FS

FIGURES_DIR = Path(__file__).parent / "output"
CUTOFFS_HZ = (40.0, 100.0)
ORDER4_CUTOFF_HZ = 100.0


def run_part_a(save: bool) -> None:
    t, x = generate_test_signal(fs=DEFAULT_FS)
    for fc in CUTOFFS_HZ:
        b, a = biquad_butterworth_bilinear(fc, DEFAULT_FS)
        y = apply_difference_equation(b, a, x)
        print(f"[A] 2do orden, fc={fc} Hz: b={np.round(b, 6)}, a={np.round(a, 6)}")
        fig = plot_before_after_spectrum(t, x, y, DEFAULT_FS, f"Filtro 2do orden manual, fc={fc:g} Hz")
        if save:
            fig.savefig(FIGURES_DIR / f"parte_a_fc{int(fc)}hz.png", dpi=150)


def run_part_b(save: bool) -> None:
    t, x = generate_test_signal(fs=DEFAULT_FS)

    sections = order4_manual_sections(ORDER4_CUTOFF_HZ, DEFAULT_FS)
    y_manual = apply_cascade(sections, x)
    b_manual, a_manual = combine_sections(sections)

    b_scipy, a_scipy, y_scipy = scipy_butter_lowpass(4, ORDER4_CUTOFF_HZ, DEFAULT_FS, x)

    max_diff = float(np.max(np.abs(y_manual - y_scipy)))
    print(f"[B] 4to orden, fc={ORDER4_CUTOFF_HZ} Hz")
    print(f"    manual b={np.round(b_manual, 6)}")
    print(f"    manual a={np.round(a_manual, 6)}")
    print(f"    scipy  b={np.round(b_scipy, 6)}")
    print(f"    scipy  a={np.round(a_scipy, 6)}")
    print(f"    max|y_manual - y_scipy| = {max_diff:.3e}")

    fig = plot_manual_vs_scipy(t, y_manual, y_scipy, f"4to orden: manual (cascada) vs. scipy, fc={ORDER4_CUTOFF_HZ:g} Hz")
    if save:
        fig.savefig(FIGURES_DIR / "parte_b_comparacion.png", dpi=150)


def main(save: bool = True, show: bool = True) -> None:
    if save:
        FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    run_part_a(save)
    run_part_b(save)

    if show:
        plt.show()


if __name__ == "__main__":
    main()
