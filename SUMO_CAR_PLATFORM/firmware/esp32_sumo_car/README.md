# esp32_sumo_car

Firmware ESP32 para el carro sumo controlado por la inclinación del celular.
El ESP32 crea su propia red WiFi (Access Point) y sirve su propia página de
control — no hay PC ni servidor Python en el loop de ejecución.

## Placa

**ESP32-S3** (p.ej. ESP32-S3-DevKitC-1 o similar). En Arduino IDE/
`arduino-cli`, selecciona la placa **"ESP32S3 Dev Module"** (no "ESP32 Dev
Module" genérico).

## Pines (L298N)

Ajusta estos `#define` al inicio de cada sketch según tu cableado real:

| Función                        | Pin ESP32-S3 |
|---------------------------------|--------------|
| IN1 (motor izquierdo, dir. A)   | 4            |
| IN2 (motor izquierdo, dir. B)   | 5            |
| IN3 (motor derecho, dir. A)     | 6            |
| IN4 (motor derecho, dir. B)     | 7            |
| ENA (PWM velocidad izquierdo)   | 15           |
| ENB (PWM velocidad derecho)     | 16           |

Rango GPIO 1–21 elegido deliberadamente, seguro para uso general en
ESP32-S3:
- Evita los **strapping pins** (GPIO 0, 3, 45, 46), que afectan el modo de
  boot si tienen un estado inesperado al encender.
- Evita los pines reservados para **flash/PSRAM integrada** (comúnmente
  GPIO 26-37 en variantes con PSRAM octal) — usarlos como salida de motor
  puede colgar el arranque o corromper el acceso a memoria.
- Evita los pines de **USB nativo** (19/20) en placas que exponen
  USB-OTG, para no interferir con la consola/flasheo por USB.

En `esp32_sumo_car.ino` la velocidad PWM ya NO es un `#define` fijo: es la
variable `motorSpeed` (default `MOTOR_SPEED_DEFAULT = 200`), ajustable en
caliente desde la página web (ver "Nuevos endpoints HTTP" más abajo). En
los sprints (`test_motor_l298n.ino`, etc.) sigue siendo una variable local
ajustable solo por Serial (`+`/`-`), sin cambios. `analogWrite()` en el
core arduino-esp32 (2.x/3.x) usa el periférico LEDC internamente — no
requiere cambios de lógica entre ESP32 clásico y ESP32-S3, solo los pines.

## UART de debug (opcional)

Además del log por USB-CDC (`Serial`, el que ves en el Monitor Serie de
Arduino IDE), los 4 sketches espejan cada línea de log a una UART de
hardware dedicada (`DebugUART`, `HardwareSerial(1)`):

| Función                | Pin ESP32-S3 |
|-------------------------|--------------|
| TX (DebugUART)          | 17           |
| RX (DebugUART)          | 18           |
| Baudrate                | 115200       |

Esta UART es **opcional**: el USB-CDC sigue funcionando igual que antes
para flashear y para los comandos interactivos (`f`/`b`/`l`/`r`/`s`/`+`/`-`
en `test_motor_l298n.ino`). Está pensada para monitoreo externo — conecta
un adaptador USB-TTL a los pines TX/RX (cruzando TX↔RX con el adaptador) y
lee el log con cualquier terminal serie normal (PuTTY, `screen`, `minicom`,
etc.), sin depender de que el puerto USB-CDC esté libre u ocupado por el
Monitor Serie de Arduino IDE.

## Red WiFi (Access Point)

- SSID: `SumoCar`
- Password: `sumo1234`
- IP fija del ESP32: `192.168.4.1` (default de `WiFi.softAP()`)

El celular debe conectarse a esta red WiFi (perderá datos móviles mientras
esté conectado) y abrir `http://192.168.4.1/` en el navegador.

## Umbrales de dirección

- `DEADZONE_DEG = 8.0`: inclinación por debajo de este valor en ambos ejes
  se considera "reposo" → `stop`.
- `THRESHOLD_DEG = 15.0`: inclinación mínima en el eje dominante para que se
  resuelva una dirección distinta de `stop`.
- Si el carro reacciona al revés (adelante cuando debería ir atrás, etc.),
  invierte el signo correspondiente en `resolveDirection()` — el signo de
  `event.beta`/`event.gamma` puede variar según el navegador/orientación
  del teléfono.

## Nuevos endpoints HTTP (solo en `esp32_sumo_car.ino`, Sprint 5)

Además de `GET /`, `POST /tilt` y `GET /tilt` (ya documentados arriba),
el sketch final expone:

| Endpoint              | Método | Body / respuesta                                                        |
|------------------------|--------|---------------------------------------------------------------------------|
| `/speed`              | POST   | body `speed=<0-255>` (url-encoded, igual estilo que `/tilt`); clampa a [0,255] y aplica el nuevo PWM de inmediato si el carro ya está en movimiento. Responde con el valor efectivo. |
| `/logs`               | GET    | JSON array de strings con las últimas ~20 líneas de eventos de control (cambios de dirección/velocidad), más recientes al final. Alimenta el panel de logs de la página. |
| `/status`             | GET    | JSON `{pitch, roll, direction, pwm, posX, posY, headingDeg, uptimeMs}`. Usado por el minimapa (polling cada ~300ms) y para sincronizar el slider de velocidad al cargar la página. |
| `/reset-position`     | POST   | Sin body. Pone `posX=posY=headingDeg=0` y reinicia el reloj interno de dead-reckoning. Usado por el botón "Reset mapa". |

La página web (`PAGE_HTML` dentro de `esp32_sumo_car.ino`) ahora incluye:
- Un slider de PWM (0-255) que llama a `POST /speed` en cada cambio.
- Un panel `<pre>`/`<div>` con scroll que hace polling a `GET /logs` cada
  1s y muestra las últimas ~20 líneas de control.
- Un `<canvas>` minimapa que hace polling a `GET /status` cada ~300ms y
  dibuja la trayectoria acumulada de la sesión (no se borra entre polls,
  solo con el botón "Reset mapa").

### Minimapa por dead-reckoning (ESTIMACIÓN, no posición real)

El carro no tiene encoders ni GPS, así que `posX`, `posY` y `headingDeg`
son una integración en lazo abierto de "PWM aplicado x tiempo transcurrido"
dentro de `updatePosition()` (llamada en cada iteración de `loop()`):

- `forward`/`backward`: avanza `posX/posY` según `headingDeg` actual, con
  velocidad lineal estimada `pwm * LINEAR_SPEED_PER_PWM_UNIT`.
- `left`/`right` (giro in-place): cambia `headingDeg` según
  `pwm * ANGULAR_SPEED_PER_PWM_UNIT` (grados/seg).
- `stop`: no cambia nada.

Esta posición **deriva y acumula error con el tiempo** — es una referencia
visual aproximada de hacia dónde se ha movido el carro, no una ubicación
precisa. Dos constantes de calibración en `esp32_sumo_car.ino` controlan la
escala de esa estimación (valores de partida razonables, hay que
calibrarlos en el hardware real):

- `LINEAR_SPEED_PER_PWM_UNIT` (m/s por unidad de PWM, default `0.0025`):
  para calibrar, corre el carro hacia adelante a un PWM fijo durante N
  segundos, mide la distancia real recorrida en metros, y calcula
  `velocidad_m_s = distancia_m / N`; luego
  `LINEAR_SPEED_PER_PWM_UNIT = velocidad_m_s / pwm`.
- `ANGULAR_SPEED_PER_PWM_UNIT` (grados/seg por unidad de PWM, default
  `0.35`): para calibrar, haz girar el carro en el mismo sitio a un PWM
  fijo, mide cuántos segundos tarda en dar una vuelta completa (360°), y
  calcula `grados_seg = 360 / segundos_por_vuelta`; luego
  `ANGULAR_SPEED_PER_PWM_UNIT = grados_seg / pwm`.

## Cómo flashear

1. Arduino IDE (o `arduino-cli`) con el core `esp32` instalado.
2. Placa: "ESP32S3 Dev Module" (o la correspondiente a tu módulo
   ESP32-S3, p.ej. ESP32-S3-DevKitC-1).
3. Abre el `.ino` deseado, selecciona el puerto COM correcto, compila y
   sube (`Sketch > Upload` o `Ctrl+U`).
4. Abre el Serial Monitor a 115200 baud para ver los logs.

## Cómo probar cada sprint

### `sprits/test_wifi_ap/test_wifi_ap.ino` (Sprint 1)
Flashea y abre el Serial Monitor: debe imprimir el SSID y la IP
(`192.168.4.1`). Conecta el celular a la red `SumoCar` y confirma que se
conecta correctamente (sin necesidad de abrir ninguna página todavía).

### `sprits/test_motor_l298n/test_motor_l298n.ino` (Sprint 2)
Con el carro sobre un soporte (ruedas sin tocar el piso), flashea y
observa la secuencia fija al arrancar: avanza, para, retrocede, para,
gira izquierda, para, gira derecha, para. Luego usa los comandos Serial
(`f`/`b`/`l`/`r`/`s`, `+`/`-` velocidad) para repetir pruebas manualmente.

### `sprits/test_webserver_tilt/test_webserver_tilt.ino` (Sprint 3 + 4)
Flashea, conecta el celular a `SumoCar`, abre `http://192.168.4.1/` en el
navegador y toca "Activar sensores" (en iOS pedirá permiso explícito).
Inclina el teléfono en las 4 direcciones y confirma en el Serial Monitor
que `pitch`/`roll` cambian y que se imprime la dirección resuelta
(`forward`/`backward`/`left`/`right`/`stop`). Cierra la pestaña del
navegador o aleja el celular y confirma que tras ~800ms se fuerza `stop`
por el watchdog.

### `esp32_sumo_car.ino` (Sprint 5 — integración final)
Con el carro en el piso, repite la prueba anterior y confirma movimiento
físico real en las 4 direcciones, parada en reposo, y parada automática al
cerrar la pestaña o perder conexión con el celular. Además, en este sketch
confirma: que el slider de PWM cambia la velocidad real del carro en
movimiento; que el panel de logs de la página muestra las últimas líneas
de `applyDirection()`; y que el minimapa dibuja una trayectoria al mover
el carro y se limpia (junto con `posX/posY/headingDeg`) al tocar "Reset
mapa" — recordando que esa posición es una estimación aproximada
(dead-reckoning), no una medición real.
