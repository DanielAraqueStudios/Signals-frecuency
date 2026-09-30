"""Decode every Muestra*.csv under ../PUNTO_3/Muestras using the 16-level
AM/nibble-pair format, printing and plotting the result for each.

Usage:
    python main.py                      # decode all MuestraXX.csv found
    python main.py Muestra01.csv        # decode a single file by name
"""

from __future__ import annotations

import sys
from pathlib import Path

from decode_lab.data import load_signal
from decode_lab.envelope import am_envelope
from decode_lab.pipeline import decode_csv
from decode_lab.plotting import plot_decode
from decode_lab.symbols import calibrate, symbol_averages

MUESTRAS_DIR = Path(__file__).resolve().parent.parent / "PUNTO_3" / "Muestras"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def decode_and_report(csv_path: Path) -> None:
    result = decode_csv(csv_path)

    print(f"--- {csv_path.name} ---")
    print(f"fs = {result.sample_rate_hz:.3f} Hz, {result.n_symbols_total} symbolos totales, "
          f"{result.n_data_symbols} simbolos de datos")
    print(f"portadora medida por FFT: {result.carrier_hz:.2f} Hz, "
          f"frecuencia de corte usada: {result.cutoff_hz:.2f} Hz")
    print(f"calibracion: nivel = {result.calibration_slope:.5f}*avg + "
          f"{result.calibration_intercept:.5f} (residuo max = "
          f"{result.calibration_max_abs_residual:.3f} niveles)")
    print(f"terminador 0x00 encontrado: {result.terminator_found}")
    print(f"bytes ({len(result.byte_values)}): {[hex(b) for b in result.byte_values]}")
    print(f"texto: {result.text!r}")
    print(f"texto (agrupado, formato de codigo): {result.text_grouped}")
    print()

    OUTPUT_DIR.mkdir(exist_ok=True)
    t, amplitude, fs = load_signal(csv_path)
    envelope, _, _ = am_envelope(amplitude, fs)
    avgs = symbol_averages(envelope, fs)
    slope, intercept, _ = calibrate(avgs)
    fig_path = OUTPUT_DIR / f"{csv_path.stem}_decode.png"
    plot_decode(t, envelope, avgs, slope, intercept, fig_path)


def main() -> None:
    if len(sys.argv) > 1:
        targets = [MUESTRAS_DIR / sys.argv[1]]
    else:
        targets = sorted(MUESTRAS_DIR.glob("Muestra*.csv"))

    if not targets:
        print(f"No se encontraron archivos Muestra*.csv en {MUESTRAS_DIR}")
        return

    for csv_path in targets:
        if not csv_path.exists():
            print(f"No existe: {csv_path}")
            continue
        decode_and_report(csv_path)


if __name__ == "__main__":
    main()
