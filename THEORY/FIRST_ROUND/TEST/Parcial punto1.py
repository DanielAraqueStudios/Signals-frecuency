import numpy as np
import matplotlib.pyplot as plt
import os

# Obtener la ruta de la carpeta actual donde se encuentra este archivo de Python
carpeta_actual = os.path.dirname(os.path.abspath(__file__))

# Cargar el archivo CSV usando la ruta relativa (debe estar en la misma carpeta)
ruta_csv = os.path.join(carpeta_actual, "Muestra01.csv")

if not os.path.exists(ruta_csv):
    print(f"[ERROR] No se encontró el archivo 'Muestra01.csv' en la ruta: {ruta_csv}")
    print("Asegúrate de colocarlo en la misma carpeta que este script.")
else:
    signal = np.loadtxt(ruta_csv, delimiter=",")
    fs, dt = 5000.0, 0.05
    n_samples = int(fs * dt)
    n_segs = len(signal) // n_samples
    t = np.arange(len(signal)) / fs

    # Crear una única figura con todas las gráficas una debajo de la otra (+1 para la señal en el tiempo)
    fig, axes = plt.subplots(n_segs + 1, 1, figsize=(10, 2.2 * (n_segs + 1)))

    # 1. Primera gráfica: Señal completa en el tiempo (en el primer eje)
    axes[0].plot(t, signal, color='tab:blue')
    axes[0].set_title("Señal Completa Muestra01 en el Tiempo", fontsize=10)
    axes[0].set_ylabel("Amplitud")
    axes[0].grid(True)

    # 2. Siguientes gráficas: Espectro de frecuencia por cada segmento
    for i in range(n_segs):
        seg = signal[i * n_samples : (i + 1) * n_samples]
        freqs = np.fft.rfftfreq(len(seg), 1 / fs)
        mag = np.abs(np.fft.rfft(seg)) / len(seg)
        
        peak = freqs[np.argmax(mag[1:]) + 1]
        print(f"Segmento {i+1} - Freq Dominante: {peak:.2f} Hz")
        
        # Asignar a su respectivo eje (uno debajo del otro)
        ax = axes[i + 1]
        ax.plot(freqs, mag, color='tab:orange')
        ax.set_title(f"Espectro Segmento {i+1} (Dominante: {peak:.1f} Hz)", fontsize=9)
        ax.set_ylabel("Magnitud")
        ax.grid(True)

    # Ajustes finales de etiquetas y espacios
    axes[-1].set_xlabel("Frecuencia (Hz)")
    plt.subplots_adjust(hspace=0.45)
    plt.show()