# esp32_local_http

Local-mode firmware: connects to the Android phone's WiFi hotspot, gates
the band motor behind a fingerprint check, and polls
`LOCAL_MODE/local-server`'s `GET /images/latest` over plain HTTP (no TLS,
no MQTT), showing the running state and each new classification result on
a 16x2 I2C LCD. See `../../../CLOUD_MODE/firmware/esp32s3_result_display/`
for the Railway/MQTT-mode counterpart -- same network job, different
transport and no motor/fingerprint hardware there.

Board: **ESP32-WROOM-32** (no PSRAM). GPIO16/17 are used for the
fingerprint sensor's UART2 -- free on a WROOM-32, but reserved for PSRAM
on an ESP32-WROVER, so this pin assignment would need to change on that
board.

## Hardware

- **Fingerprint sensor** (Adafruit_Fingerprint-compatible, e.g. R307/FPM10A)
  on `HardwareSerial(2)`, RX=GPIO16, TX=GPIO17, 57600 baud. Gates the band:
  a recognized fingerprint toggles the motor on/off; an unrecognized one is
  rejected and the motor state doesn't change.
- **BTS7960 H-bridge** driving the band motor, one direction only:
  `RPWM_PIN`=25, `LPWM_PIN`=26, `EN_PIN`=27. Speed (`motorSpeed`, 0-255) is
  adjustable over Serial with `+`/`-` while running.
- **16x2 I2C LCD** (PCF8574 backpack, address `0x27`), SDA=GPIO21,
  SCL=GPIO22. Shows `BANDA: ENCENDIDA`/`APAGADA` on line 1. Line 2 shows
  either the last fingerprint ID (before any result) or the latest
  classification result -- and, when a diameter measurement is also
  available (see below), alternates line 2 every 2s between the label
  (e.g. `brocas (92%)`) and the diameter (e.g. `D=1.25cm`), since both
  don't fit in 16 characters at once. The Serial log always prints the
  full, un-truncated detail (label + confidence + diameter together)
  regardless of this LCD simplification.
- **Diameter display**: `GET /images/latest`'s response may include a
  `diameter_cm` field (nullable float) computed by local-server's
  diameter-measurement module on the same photo used for classification.
  `pollLatestResult()` reads it with a `-1.0f` sentinel for "not
  available" (JSON `null` or a missing field both fall back to the
  sentinel via ArduinoJson's `| default` operator) and feeds it into both
  the Serial `Result:` line and the LCD alternation above; when not
  available, it's simply omitted rather than shown as `-1.00cm`.
- **Band pause-for-photo is triggered over the network, NOT by the
  VL53L0X distance sensor** -- that sensor isn't working reliably on this
  rig. A second device (an Android phone, fixed IP on the same LAN)
  `POST`s to `local-server`'s `/band/pause` on each volume-up/down press;
  this sketch polls `GET /band/pause-status` and pauses the band for
  `PAUSE_FOR_PHOTO_MS` (5s) exactly as it would on a sensor detection. See
  `../../local-server/app/pause_trigger.py` for the one-shot semantics
  (each button press = exactly one pause). Only pauses while the
  fingerprint-authorized `motorOn` is true -- it never changes that
  authorization itself. The VL53L0X wiring/code is kept working and
  isolated in `sprits/test_distance_sensor/` for whenever the sensor
  itself gets fixed and this can switch back.

## Before flashing

WiFi SSID/password are **not** edited into the sketch -- they're entered
once over the Arduino Serial Monitor at boot and saved to the board's NVS
(flash) via the `Preferences` library, so the exact same compiled binary
can be pointed at the Android phone's hotspot today, a different hotspot
tomorrow, or any other 2.4GHz network, without reflashing. On a board
with nothing stored yet, first boot prints "No WiFi credentials stored
yet." and prompts for SSID then password over Serial (115200 baud); on
later boots it shows the stored SSID and gives you 5 seconds to send `c`
if you want to change network, otherwise it reuses what's stored. The
hotspot must stay on 2.4GHz/compatibility mode -- most ESP32 boards can't
see a 5GHz-only hotspot.

Still edit this constant at the top of the `.ino` (rarely changes between
networks):

- `LOCAL_SERVER_HOST` -- the local-server machine's LAN IP. See
  `../../NETWORK_SETUP.md` for how to determine a stable value on a
  phone hotspot (DHCP reservation generally isn't available like on a
  router); there's no discovery mechanism here yet.
- `LOCAL_SERVER_PORT` -- default `8100`, matching
  `../../local-server/README.md`'s `uvicorn` example.

The sensor must be detected at boot (`finger.verifyPassword()`) or the
sketch halts with `ERROR: sensor no encontrado` on the LCD -- check
wiring and that the sensor is powered at 3V3, not 5V.

## Setting up the pause-trigger phone (device #2)

This phone is separate from the one taking photos. It needs a fixed IP on
the same LAN (so it's reachable the same way every time -- see
`../../NETWORK_SETUP.md`) and something that fires an HTTP request when
its volume-up or volume-down button is pressed. This sketch and
local-server don't care how that happens on the phone side -- any app
that can map a hardware button to an HTTP request works (e.g. Tasker,
Automate, Button Mapper + an HTTP-shortcut app). Configure it to send:

```
POST http://<local-server LAN IP>:8100/band/pause
```

(no body needed) on both volume-up and volume-down. Each press pauses
the band for 5 seconds, exactly as the VL53L0X would on detecting a part.

## Serial menu (fingerprint enrollment + motor speed)

Available any time after boot, over the Serial Monitor (115200 baud):

| Command | Effect |
|---|---|
| `a` | show the menu again |
| `l` | list occupied fingerprint IDs |
| `n` | enroll a new fingerprint at the next free ID |
| `r <id>` | enroll a fingerprint at a specific ID (e.g. `r 5`) |
| `b <id>` | delete a specific fingerprint ID (e.g. `b 5`) |
| `vaciar` | delete ALL stored fingerprints (asks to confirm with `si`) |
| `+` / `-` | increase / decrease band motor speed |

## Libraries required

- `WiFi.h`, `HTTPClient.h`, `Preferences.h`, `Wire.h` (bundled with
  Arduino-ESP32 core)
- `ArduinoJson` (install via Library Manager)
- `LiquidCrystal_I2C` (install via Library Manager)
- `Adafruit_Fingerprint` (install via Library Manager)

`Adafruit_VL53L0X` is only needed for `sprits/test_distance_sensor/`, not
for this main sketch (see "Hardware" above).

Board package: **Arduino-ESP32 core 3.x** (same requirement as the
cloud-mode sketch and `LAB_TESTING/LAB1/firmware`).

## What could not be verified

Not compiled or flashed in this environment -- no Arduino
IDE/arduino-cli or physical ESP32 hardware was available. The
`local-server` side of this flow (FastAPI app + spectrum classifier) was
run and tested directly (see `../../local-server/README.md`); the
firmware's HTTP-poll loop, JSON parsing logic, Serial/`Preferences`-based
WiFi credential flow, fingerprint enrollment/matching logic, LCD/motor
control, and the VL53L0X pause-for-photo logic are all unverified against
real hardware as an integrated whole -- each module was however verified
independently working on real hardware via the standalone sketches in
`sprits/` (`test_fingerprint`, `test_lcd`, `test_motor`, `test_wifi`,
`test_distance_sensor`) before being merged here.
