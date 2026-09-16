# esp32_local_http

Local-mode firmware: connects to the predefined WiFi access point and
polls `LOCAL_MODE/local-server`'s `GET /images/latest` over plain HTTP
(no TLS, no MQTT), printing each new classification result to Serial
(and optionally an SSD1306 OLED). See
`../../../CLOUD_MODE/firmware/esp32s3_result_display/` for the
Railway/MQTT-mode counterpart -- same board target and display logic,
different transport.

## Before flashing

Edit these constants at the top of the `.ino`:

- `WIFI_SSID` / `WIFI_PASSWORD` -- the predefined local access point,
  shared by the phone, this board, and the local-server computer.
- `LOCAL_SERVER_HOST` -- the local-server machine's LAN IP. Must be
  static or DHCP-reserved; there's no discovery mechanism here.
- `LOCAL_SERVER_PORT` -- default `8100`, matching
  `../../local-server/README.md`'s `uvicorn` example.

Optionally uncomment `#define HAS_OLED` if an SSD1306 is wired (I2C,
address `0x3C`).

## Libraries required

- `WiFi.h`, `HTTPClient.h` (bundled with Arduino-ESP32 core)
- `ArduinoJson` (install via Library Manager)
- `Adafruit_GFX` + `Adafruit_SSD1306` only if `HAS_OLED` is defined

Board package: **Arduino-ESP32 core 3.x** (same requirement as the
cloud-mode sketch and `LAB_TESTING/LAB1/firmware`).

## What could not be verified

Not compiled or flashed in this environment -- no Arduino
IDE/arduino-cli or physical ESP32 hardware was available. The
`local-server` side of this flow (FastAPI app + spectrum classifier) was
run and tested directly (see `../../local-server/README.md`); only the
firmware's HTTP-poll loop and JSON parsing logic is unverified against
real hardware.
