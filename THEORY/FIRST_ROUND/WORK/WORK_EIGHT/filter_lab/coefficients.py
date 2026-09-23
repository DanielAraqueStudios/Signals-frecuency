"""Hand-derived Butterworth low-pass coefficients via the bilinear transform.

No `scipy.signal.butter` (or any other filter-design convenience function)
anywhere in this module — every coefficient below comes from evaluating a
closed-form expression obtained by hand. The derivation (see `readme.md`
for the full algebra) is:

1. Normalized analog Butterworth low-pass prototype of order N, cutoff
   `wc` (rad/s): a product of `N/2` quadratic sections (N even)

       H(s) = prod_i  wc^2 / (s^2 + d_i*wc*s + wc^2)

   where `d_i = 2*sin((2i-1)*pi/(2N))` for `i = 1..N/2` is each section's
   damping coefficient (`d = sqrt(2)` is the single N=2 case).

2. Frequency pre-warping so the *digital* cutoff lands exactly on `fc`:

       wc = 2*fs*tan(pi*fc/fs)

3. Bilinear transform `s = K*(1 - z^-1)/(1 + z^-1)`, `K = 2*fs`, substituted
   into each quadratic section and simplified (dividing through by the
   `z^0` coefficient) gives, per section, with `C = K/wc`:

       a0' = C^2 + d*C + 1
       b0  = 1 / a0'
       b1  = 2 / a0'
       b2  = 1 / a0'
       a1  = 2*(1 - C^2) / a0'
       a2  = (C^2 - d*C + 1) / a0'

   (`a0` is normalized to 1, matching the `scipy.signal.lfilter`
   convention: `a[0]*y[n] = b @ x[n:n-3:-1] - a[1:] @ y[n-1:n-3:-1]`.)

A 2nd-order filter is exactly one such section (`d = sqrt(2)`, item A). A
4th-order Butterworth is the cascade of two sections with
`d_1 = 2*sin(pi/8)` and `d_2 = 2*sin(3*pi/8)` (item B); cascading two
sections in series is equivalent, algebraically, to convolving their
`(b, a)` polynomials into a single 4th-order transfer function.
"""

from __future__ import annotations

import numpy as np

SQRT2 = float(np.sqrt(2.0))


def _prewarp(fc: float, fs: float) -> float:
    """Pre-warped analog cutoff `wc` (rad/s) for cutoff `fc` at rate `fs`."""
    if not 0 < fc < fs / 2:
        raise ValueError(f"fc={fc} must be within (0, fs/2={fs / 2})")
    return 2.0 * fs * np.tan(np.pi * fc / fs)


def biquad_butterworth_bilinear(fc: float, fs: float, damping: float = SQRT2) -> tuple[np.ndarray, np.ndarray]:
    """One 2nd-order Butterworth low-pass section, via the bilinear transform.

    Args:
        fc: Cutoff frequency, Hz.
        fs: Sample rate, Hz.
        damping: The quadratic section's damping coefficient `d` (`sqrt(2)`
            for a standalone 2nd-order filter; `2*sin((2i-1)*pi/8)` for one
            of the two sections of a 4th-order cascade).

    Returns:
        `(b, a)`, each length-3, `a[0] == 1` — direct-form-II coefficients
        usable with `apply_difference_equation` or `scipy.signal.lfilter`.
    """
    wc = _prewarp(fc, fs)
    C = (2.0 * fs) / wc
    a0p = C**2 + damping * C + 1.0

    b = np.array([1.0, 2.0, 1.0]) / a0p
    a = np.array([
        1.0,
        2.0 * (1.0 - C**2) / a0p,
        (C**2 - damping * C + 1.0) / a0p,
    ])
    return b, a


def order4_manual_sections(fc: float, fs: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """The two 2nd-order sections making up a manual 4th-order Butterworth LPF.

    Section damping coefficients are the N=4 Butterworth pole-angle values
    `d_i = 2*sin((2i-1)*pi/8)` for `i = 1, 2`.

    Returns:
        `[(b1, a1), (b2, a2)]`; apply in cascade (see `apply.apply_cascade`)
        or combine into one 4th-order system with `np.convolve(b1, b2)`
        and `np.convolve(a1, a2)`.
    """
    d1 = 2.0 * np.sin(np.pi / 8.0)       # ~0.765367
    d2 = 2.0 * np.sin(3.0 * np.pi / 8.0)  # ~1.847759
    return [
        biquad_butterworth_bilinear(fc, fs, damping=d1),
        biquad_butterworth_bilinear(fc, fs, damping=d2),
    ]


def combine_sections(sections: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    """Collapse cascaded biquad sections into one direct-form `(b, a)` pair."""
    b = np.array([1.0])
    a = np.array([1.0])
    for bi, ai in sections:
        b = np.convolve(b, bi)
        a = np.convolve(a, ai)
    return b, a
