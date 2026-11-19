# SUMO_CAR_PLATFORM

Carro sumo controlado de forma remota por el acelerómetro/orientación de un
celular. A diferencia de otros proyectos de este repo, **el PC no participa
en tiempo de ejecución**: no hay servidor Python, no hay FastAPI. El propio
ESP32 es el servidor — crea su propia red WiFi (Access Point) y sirve él
mismo la página de control. El celular solo es el cliente que abre esa
página en el navegador. El PC solo se usa para compilar y flashear por USB.

## Arquitectura

- **Red**: ESP32 como Access Point (`WiFi.softAP`), IP fija `192.168.4.1`.
  El celular se conecta directamente a esa red (sin depender de su propio
  hotspot ni de un router externo).
- **Servidor**: `WebServer.h` (nativo del core arduino-esp32, sin librerías
  externas) sirve una página HTML/JS inline que captura
  `window.deviceorientation` y hace `POST /tilt` cada ~150-250ms.
- **Control**: inclinar el celular adelante/atrás/izquierda/derecha mueve el
  carro en esa dirección, vía un puente H L298N sobre dos motores DC.
- **Resolución de dirección**: umbrales + dead-zone central, eligiendo el
  eje dominante (pitch vs roll) cuando hay inclinación diagonal.
- **Seguridad**: si el ESP32 no recibe un `POST /tilt` fresco en más de
  ~800ms (celular bloqueado, pestaña cerrada, WiFi perdido), se fuerza
  `stop` automáticamente. Todo el loop es no bloqueante (`millis()`, sin
  `delay()` en el camino de red/motor).

## Sprints

El firmware se construyó por funcionalidad, siguiendo el mismo patrón
`sprits/` usado en `PARTS_SORTING_PLATFORM`:

1. **Sprint 1** — `firmware/esp32_sumo_car/sprits/test_wifi_ap/`: el ESP32
   levanta el Access Point y confirma SSID/IP.
2. **Sprint 2** — `firmware/esp32_sumo_car/sprits/test_motor_l298n/`:
   control directo del L298N (avanza/retrocede/gira izq/gira der/stop), sin
   red.
3. **Sprint 3 + 4** — `firmware/esp32_sumo_car/sprits/test_webserver_tilt/`:
   servidor HTTP embebido + página de inclinación + resolución de
   dirección por Serial (sin motores todavía).
4. **Sprint 5** — `firmware/esp32_sumo_car/esp32_sumo_car.ino`: integración
   final — red + servidor + resolución de dirección + control real del
   L298N.

Ver `firmware/esp32_sumo_car/README.md` para pines, cómo flashear y cómo
probar cada sprint.
