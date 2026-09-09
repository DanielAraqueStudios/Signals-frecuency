# esp32s3_result_display firmware

Arduino sketch for the ESP32-S3 device in the parts-sorting pipeline (see
`../../docs/architecture.md` and `../../mqtt-broker/README.md`). This board
is **not** the camera and does **not** run the classifier -- a worker's
phone takes the photo and uploads it over HTTPS (`api-gateway`). This
sketch's only job: connect to WiFi, connect to the MQTT broker over TLS
(MQTTS, port 8883), subscribe to this device's own result topic
(`results/<MQTT_USERNAME>`), and display/log each incoming classification
result. No physical sorting/actuation in this version -- identification
and logging only.

## Board package required: Arduino-ESP32 core **3.x**

Same requirement as `LAB_TESTING/LAB1/firmware/README.md` elsewhere in
this repo. This sketch does not use the hardware-timer API at all (it's
I/O-driven, not sampling-driven -- periodic MQTT reconnect checks use
`millis()`, not a hardware timer), so there is no timer-API version
dependency here specifically, but install core **3.x** anyway for
consistency with the rest of this repo's ESP32 firmware and because that
is the version this was written and reviewed against.

Install via Arduino IDE: Boards Manager -> "esp32" by Espressif Systems,
version 3.x -> board "ESP32S3 Dev Module" (or your exact S3 board variant).

## Required Arduino Library Manager installs

| Library | Used for |
|---|---|
| `PubSubClient` (by Nick O'Leary) | MQTT client |
| `ArduinoJson` (by Benoit Blanchon, v6 or v7) | Parsing the JSON result payload |
| `Adafruit SSD1306` + `Adafruit GFX Library` | Only if you enable `HAS_OLED` |

`WiFi.h` and `WiFiClientSecure.h` ship with the ESP32 board package
itself -- no separate install needed.

## Configuration (`#define`s at the top of the .ino)

| Define | Meaning |
|---|---|
| `WIFI_SSID`, `WIFI_PASSWORD` | Your WiFi credentials |
| `MQTT_HOST` | Broker hostname/IP |
| `MQTT_PORT` | `8883` (TLS-only, per `mqtt-broker/README.md`) |
| `MQTT_USERNAME` | This device's MQTT login, `device-<deviceId>` -- also the topic segment this sketch subscribes to (`results/<MQTT_USERNAME>`). Do not change the topic scheme; see `../../mqtt-broker/README.md` "Topic scheme" for why it's shaped this way (no `userId` in the topic, ownership is tracked in `api-gateway`'s database instead). |
| `MQTT_PASSWORD` | This device's MQTT password |
| `MQTT_CA_CERT` | PEM of the broker's CA certificate, embedded as a `PROGMEM` string |
| `HAS_OLED` (commented out by default) | Uncomment to enable optional SSD1306 OLED output alongside Serial |

### Where to get WiFi / MQTT credentials and the CA cert

- **Local dev**: run `../../scripts/gen-dev-certs.sh` from the repo root
  (see that script and `../../mqtt-broker/README.md` "Local dev"). It
  writes `mqtt-broker/certs/ca.crt` -- paste that file's contents into
  `MQTT_CA_CERT`. Create a matching device login with
  `mosquitto_passwd -b ... device-deviceABC devpassword2` (same README) and
  use `device-deviceABC` / `devpassword2` as `MQTT_USERNAME` /
  `MQTT_PASSWORD`.
- **Production**: `api-gateway`'s planned `POST /devices/pair` endpoint
  (see `../../docs/deployment-railway.md` / the root plan) is meant to
  issue a real device its own MQTT username/password and topic scope when
  a logged-in user pairs a physical ESP32-S3 to their account. That
  endpoint is not built yet in this pass -- until it exists, provision
  credentials the same way as local dev, against whatever broker instance
  you're pointed at, and paste in that broker's real CA cert (or the
  public CA chain, if the broker uses a publicly-trusted certificate
  instead of a self-signed dev one).

## Wiring

Minimal -- this device has no camera and does no sensing in this project.

- **Power**: USB or 5V/3V3 per your ESP32-S3 board's usual supply.
- **Optional OLED** (only if `HAS_OLED` is defined): SSD1306 over I2C,
  `SDA` -> default I2C SDA pin for your ESP32-S3 board, `SCL` -> default
  I2C SCL pin, `VCC` -> 3V3, `GND` -> GND, I2C address `0x3C` (the common
  default -- change `OLED_I2C_ADDRESS` in the sketch if yours differs).
  Check your specific ESP32-S3 board's pinout silkscreen/datasheet for
  which physical pins map to the default `Wire.begin()` SDA/SCL, since
  this varies more across S3 dev boards than on classic ESP32-WROOM.

## The PubSubClient buffer-size trap (already fixed in this sketch, worth knowing)

`PubSubClient`'s default MQTT packet buffer is **256 bytes**. A JSON
result payload (label + confidence + stub flag, plus any fields added
later) can exceed that, and when it does, PubSubClient does not raise an
error -- it just silently never invokes the message callback for that
publish, which reads like "nothing is arriving" rather than "the message
was too big." This sketch calls `mqttClient.setBufferSize(512)` in
`setup()`, before the first `connect()`, to avoid that trap. If you add
more fields to the result payload later and messages start silently
vanishing again, this is the first thing to check.

## Serial output

On each incoming result, prints e.g.:

```
Result: STUB: unclassified
--- running counts ---
  unclassified: 3
-----------------------
```

or, once a real trained model exists (`stub:false`):

```
Result: bolt (94%)
--- running counts ---
  bolt: 12
  screw: 4
-----------------------
```

## What could not be verified

**No physical ESP32-S3 hardware and no Arduino IDE/`arduino-cli` compiler
were available in this environment.** `arduino-cli version` was checked
and is not installed here, so this sketch has **not** been compiled, let
alone flashed or run against a real broker. This matches how
`LAB_TESTING/LAB1/firmware/README.md` and
`THEORY/FIRST_ROUND/TEST/firmware/README.md` both state upfront when
something wasn't tested on real hardware -- same honesty policy applies
here. Before relying on this:

- Compile it in the Arduino IDE against an "ESP32S3 Dev Module" board
  profile (or your exact variant) with core 3.x installed, and fix any
  real compile errors that turn up (library API surfaces do shift between
  minor versions).
- Point it at a real broker (the local dev one from
  `../../mqtt-broker/README.md` is enough) and confirm the TLS handshake
  succeeds, `MQTT: connected` / `MQTT: subscribed to results/...` print,
  and a `mosquitto_pub` of a sample result JSON (see that README's
  "publish" example) shows up correctly formatted on Serial.
- If you enable `HAS_OLED`, verify the display actually shows the result
  -- OLED wiring/address issues fail silently into the "WARN: SSD1306
  OLED not found, continuing Serial-only" path rather than crashing, so
  double check on real hardware, not just by reading the code.
