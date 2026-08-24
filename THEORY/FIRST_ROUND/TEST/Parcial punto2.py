import numpy as np
import matplotlib.pyplot as plt

# Parámetros de la señal original
f_signal = 100.0  # Frecuencia de la sinusoide (100 Hz)
duracion = 0.05   # Duración de la señal en segundos
t_alta = np.linspace(0, duracion, 10000)
senal_original = np.sin(2 * np.pi * f_signal * t_alta)

# Frecuencias de muestreo solicitadas
frecuencias_muestreo = [70, 500, 1000] # en Hz

# Algoritmo de cuantización por niveles (DAC)
def cuantizar(senal, bits=3):
    niveles = 2 ** bits
    senal_norm = (senal + 1) / 2  # Normalizar entre 0 y 1
    cuantizada = np.round(senal_norm * (niveles - 1)) / (niveles - 1)
    return cuantizada * 2 - 1     # Regresar a escala -1 a 1

# Crear figura con mejor espacio vertical (hspace)
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

for i, fs_m in enumerate(frecuencias_muestreo):
    # Vector de tiempo discretizado
    t_muestras = np.arange(0, duracion, 1 / fs_m)
    senal_muestra = np.sin(2 * np.pi * f_signal * t_muestras)
    
    # Cuantización
    senal_cuantizada = cuantizar(senal_muestra, bits=3)
    
    # Graficar en cada subgráfica de forma limpia
    ax = axes[i]
    ax.plot(t_alta, senal_original, 'k:', alpha=0.25, label='Señal Analógica Original')
    ax.stem(t_muestras, senal_cuantizada, linefmt=f'C{i}-', markerfmt=f'C{i}o', 
             basefmt='k-', label=f'Muestreada y Cuantizada (fs = {fs_m} Hz)')
    
    ax.set_title(f'Frecuencia de Muestreo: {fs_m} Hz', fontsize=10)
    ax.set_ylabel('Amplitud')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', fontsize=9)
    ax.set_ylim(-1.3, 1.3)

axes[-1].set_xlabel('Tiempo (s)')
plt.subplots_adjust(hspace=0.3) # Espaciado limpio para evitar líneas cruzadas
plt.show()