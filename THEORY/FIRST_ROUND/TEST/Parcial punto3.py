import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import os

# Obtener la ruta de la carpeta actual donde se encuentra este archivo de Python
carpeta_actual = os.path.dirname(os.path.abspath(__file__))

# Definir los archivos usando rutas relativas dentro de la misma carpeta
archivos = {
    'Violín': os.path.join(carpeta_actual, 'violin.wav'),
    'Tambor': os.path.join(carpeta_actual, 'tambor.wav'),
    'Gato': os.path.join(carpeta_actual, 'gato.wav')
}

plt.figure(figsize=(12, 6))

for nombre, ruta_completa in archivos.items():
    if os.path.exists(ruta_completa):
        try:
            # Leer el archivo de audio real
            fs, audio = wavfile.read(ruta_completa)
            
            # Si el audio es estéreo (2 canales), tomamos solo un canal
            if len(audio.shape) > 1:
                audio = audio[:, 0]
                
            # Normalizar el audio
            audio = audio / np.max(np.abs(audio))
            
            # Aplicar Transformada Rápida de Fourier (FFT)
            n = len(audio)
            fft_val = np.fft.rfft(audio)
            fft_freq = np.fft.rfftfreq(n, 1 / fs)
            mag = np.abs(fft_val) / n
            
            # Graficar el espectro de frecuencia
            plt.plot(fft_freq, mag, label=f'{nombre} (Fs: {fs} Hz)', alpha=0.7)
            print(f"[ÉXITO] Cargado exitosamente: {nombre} | Frecuencia de muestreo: {fs} Hz")
            
        except Exception as e:
            print(f"[ERROR] El archivo '{nombre}' falló al leerse. Detalle: {e}")
    else:
        print(f"[NO ENCONTRADO] No se encontró el archivo '{nombre}' en: {ruta_completa}")

plt.title('Punto 3: Análisis de Espectro de Frecuencias con Audios Reales')
plt.xlabel('Frecuencia (Hz)')
plt.ylabel('Magnitud Normalizada')
plt.xlim(0, 4000) # Rango de frecuencia para visualizar mejor los componentes
plt.grid(True)
plt.legend()
plt.show()