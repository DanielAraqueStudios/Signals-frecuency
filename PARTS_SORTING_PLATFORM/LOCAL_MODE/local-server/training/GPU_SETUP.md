# Entrenar con GPU

`train.py` ya soporta GPU (detecta CUDA automáticamente, o puedes forzarlo
con `--device 0` / `--device cpu`). Lo que falta para que realmente use la
GPU es instalar la versión correcta de **PyTorch** -- `pip install -r
requirements-training.txt` por sí solo instala la build de **CPU** de
torch como dependencia de `ultralytics`, nunca la de CUDA.

## Cómo saber con certeza si vas a entrenar con GPU

No asumas que "porque tengo una GPU" ya va a usarse -- `train.py` cae a
CPU **en silencio** si torch no tiene soporte CUDA instalado. Para
confirmarlo explícitamente:

```bash
python check_gpu.py
```

Esto revisa (1) si el driver NVIDIA responde (`nvidia-smi`) y (2) si
`torch.cuda.is_available()` es `True` -- que es lo único que realmente
importa para el entrenamiento. Te dice claramente "GPU lista" o qué falta.

Además, `train.py --require-gpu` falla con error en vez de entrenar en
CPU si no detecta GPU -- úsalo si querés estar 100% seguro de que nunca
se te va en CPU por accidente (ej. si olvidaste instalar el torch CUDA).

## Tu hardware detectado en este entorno

Se verificó `nvidia-smi` en esta máquina (sesión de desarrollo, no
necesariamente la máquina donde vas a entrenar realmente):

- GPU: **GeForce GTX 1650**, 4096 MiB VRAM
- Driver: 462.30 (reporta soporte hasta CUDA 11.2)
- `torch` **no estaba instalado** -- sin instalarlo, el entrenamiento cae
  a CPU sin avisar.

Implicaciones para tus parámetros de entrenamiento si esta es la GPU real:
- 4GB VRAM es poco -- usa `--batch 8` o menos (el default del script es
  16) y considera `--imgsz 416` en vez de 640 si te quedas sin memoria
  (`CUDA out of memory`).
- El driver 462.30 es relativamente antiguo (de la era CUDA 11.x). Los
  builds más nuevos de PyTorch (cu121, cu124...) pueden requerir un
  driver más reciente que el tuyo -- si el paso 1 de abajo falla o
  `torch.cuda.is_available()` sigue dando `False` después de instalar,
  lo más probable es que necesites **actualizar el driver NVIDIA** desde
  nvidia.com antes de que cualquier build de torch con CUDA funcione.
  [VERIFICAR: la compatibilidad exacta driver-CUDA depende de la versión
  de PyTorch que elijas -- revisa la tabla en
  https://pytorch.org/get-started/locally/ antes de instalar].

## Requisitos

- Una GPU **NVIDIA** (CUDA). AMD/Intel no están soportados por esta ruta
  (PyTorch tiene soporte experimental ROCm para AMD en Linux, pero no está
  cubierto aquí -- [VERIFICAR CONTRA LA DOCUMENTACIÓN DE PYTORCH SI APLICA
  A TU HARDWARE]).
- Drivers NVIDIA actualizados instalados en el sistema (no solo el
  toolkit CUDA -- el driver). Verifica con `nvidia-smi` en una terminal;
  si no reconoce la tarjeta, instala/actualiza el driver desde NVIDIA
  antes de seguir.

## Pasos (Windows/Linux, en este orden)

1. **Antes** de instalar `requirements-training.txt`, instala PyTorch con
   soporte CUDA desde el índice oficial de PyTorch (no desde PyPI normal).
   La URL exacta del índice depende de tu versión de CUDA -- la página
   oficial (https://pytorch.org/get-started/locally/) te da el comando
   exacto según tu sistema. Ejemplo típico (CUDA 12.1, verificar contra
   tu propia versión antes de copiar literal):

   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

2. Luego instala el resto normalmente:

   ```bash
   pip install -r requirements-training.txt
   ```

   Esto no debería reinstalar/downgradear el torch con CUDA que ya
   pusiste en el paso 1, porque `requirements-training.txt` no fija una
   versión de `torch` directamente (lo trae `ultralytics` como
   dependencia, y pip respeta la versión ya instalada si satisface el
   rango). Si notás que sí lo reemplaza por una build CPU, repetí el
   paso 1 después del paso 2.

3. Verifica que Python ve la GPU:

   ```bash
   python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'sin GPU')"
   ```

   Debe imprimir `True` y el nombre de tu tarjeta. Si imprime `False`,
   el entrenamiento caerá a CPU automáticamente (train.py detecta esto
   solo) -- revisa el paso 1 y los drivers antes de reportar un bug.

4. Corre el entrenamiento normal -- ya se usa la GPU automáticamente:

   ```bash
   python train.py
   ```

   O desde los scripts de conveniencia: `python ../../scripts/run_training.py`.

## Notas

- `run_training.py` (en `../../scripts/`) solo instala
  `requirements-training.txt` si `ultralytics` no está disponible -- no
  instala torch con CUDA por ti. Ese paso 1 de arriba es manual y
  deliberado: la URL del índice de PyTorch depende de la versión de CUDA
  instalada en tu máquina, algo que este repo no puede adivinar por vos.
- Si tenés varias GPUs y querés usar una específica, `--device 1`,
  `--device 2`, etc. (índice según `nvidia-smi`).
- No verificado en este entorno -- no había GPU NVIDIA disponible para
  probar el flujo completo. Los comandos de instalación siguen la
  documentación oficial de PyTorch al momento de escribir esto, pero
  **verificá la URL del índice CUDA contra tu propia versión antes de
  copiarla literal**.
