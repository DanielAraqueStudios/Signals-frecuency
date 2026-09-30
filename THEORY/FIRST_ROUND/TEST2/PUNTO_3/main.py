"""Entry point: generates the synthetic image, applies the three original
kernels (+ bandpass cascade) plus the new zero-sum kernel, saves everything
to output/."""

from pathlib import Path

import cv2

from image_filter_lab.filtering import aplicar_cascada_pasa_bandas, aplicar_kernel
from image_filter_lab.generar_imagen import generar_imagen_sintetica
from image_filter_lab.kernels import (
    kernel_nuevo_suma_cero,
    kernel_pasa_altas00,
    kernel_pasa_altas02,
    kernel_pasa_bajas,
)
from image_filter_lab.plotting import guardar_resultado

OUTPUT_DIR = Path(__file__).parent / "output"
IMAGE_PATH = Path(__file__).parent.parent / "muestras" / "imagen.jpg"


def cargar_imagen():
    """Real image (grayscale) if present; synthetic fallback otherwise."""
    if IMAGE_PATH.exists():
        img = cv2.imread(str(IMAGE_PATH), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            print(f"Usando imagen real: {IMAGE_PATH}")
            return img
    print("Imagen real no encontrada; usando imagen sintetica de respaldo")
    return generar_imagen_sintetica(256)


def main() -> None:
    imagen = cargar_imagen()
    guardar_resultado(imagen, "Imagen original", OUTPUT_DIR / "00_original.png")

    print(f"kernel_pasa_bajas.sum()    = {kernel_pasa_bajas.sum():.6f}")
    print(f"kernel_pasa_altas00.sum()  = {kernel_pasa_altas00.sum():.6f}")
    print(f"kernel_pasa_altas02.sum()  = {kernel_pasa_altas02.sum():.6f}")
    print(f"kernel_nuevo_suma_cero.sum() = {kernel_nuevo_suma_cero.sum():.6f}")

    filtrada_bajas = aplicar_kernel(imagen, kernel_pasa_bajas)
    guardar_resultado(filtrada_bajas, "Filtro Pasa Bajas", OUTPUT_DIR / "01_pasa_bajas.png")

    filtrada_altas00 = aplicar_kernel(imagen, kernel_pasa_altas00)
    guardar_resultado(filtrada_altas00, "Filtro Pasa Altas 00", OUTPUT_DIR / "02_pasa_altas00.png")

    filtrada_altas02 = aplicar_kernel(imagen, kernel_pasa_altas02)
    guardar_resultado(filtrada_altas02, "Filtro Pasa Altas 02", OUTPUT_DIR / "03_pasa_altas02.png")

    filtrada_bandas = aplicar_cascada_pasa_bandas(imagen, kernel_pasa_bajas, kernel_pasa_altas02)
    guardar_resultado(filtrada_bandas, "Filtro Pasa Bandas (bajas + altas02)", OUTPUT_DIR / "04_pasa_bandas.png")

    filtrada_nueva = aplicar_kernel(imagen, kernel_nuevo_suma_cero)
    guardar_resultado(filtrada_nueva, "Kernel nuevo (suma cero)", OUTPUT_DIR / "05_kernel_nuevo.png")

    print(f"Resultados guardados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
