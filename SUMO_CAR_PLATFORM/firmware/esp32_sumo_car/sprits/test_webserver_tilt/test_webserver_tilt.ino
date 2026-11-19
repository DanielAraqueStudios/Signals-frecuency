/*
 * Standalone bring-up sketch: embedded HTTP server + phone tilt capture
 * + direction resolution (Sprint 3 + Sprint 4 merged).
 *
 * Board: ESP32-S3 (e.g. ESP32-S3-DevKitC-1). No H-bridge yet -- this sketch only
 * verifies that:
 *   1) the ESP32 can serve its own HTML/JS page (no PC, no external files),
 *   2) the phone's browser can read deviceorientation and POST it here,
 *   3) the firmware resolves pitch/roll into forward/backward/left/right/
 *      stop with a dead-zone and a "stale data -> stop" watchdog.
 *
 * Uses WebServer.h, which ships with the arduino-esp32 core -- no external
 * libraries required.
 *
 * Open the Serial Monitor at 115200 baud, then connect your phone to the
 * SumoCar WiFi network and browse to http://192.168.4.1/
 *
 * iOS 13+ requires an explicit user gesture before deviceorientation data
 * is released (DeviceOrientationEvent.requestPermission()); the page's
 * "Activar sensores" button handles that, same pattern as camera.html's
 * permission prompt in the previous project.
 *
 * Diagnostic logs are mirrored to both the USB-CDC Serial Monitor and a
 * dedicated hardware UART (DebugUART), so they can also be read from an
 * external USB-TTL adapter independent of the USB-CDC port.
 */

#include <WiFi.h>
#include <WebServer.h>

#define AP_SSID "SumoCar"
#define AP_PASSWORD "sumo1234"

// Direction resolution tuning (degrees). Adjust if the car feels too
// twitchy (raise DEADZONE/THRESHOLD) or too sluggish (lower them).
#define DEADZONE_DEG 8.0
#define THRESHOLD_DEG 15.0

// If no fresh /tilt POST arrives within this window, force "stop".
#define WATCHDOG_MS 800

// Dedicated hardware UART for debug logging only. Pins chosen within the
// safe GPIO 1-21 range, clear of the L298N pins used elsewhere in this
// project (4,5,6,7,15,16) and of strapping/flash-PSRAM/native-USB pins.
#define DEBUG_UART_TX_PIN 17
#define DEBUG_UART_RX_PIN 18
#define DEBUG_UART_BAUD 115200
HardwareSerial DebugUART(1);

WebServer server(80);

float lastPitch = 0;
float lastRoll = 0;
unsigned long lastTiltMs = 0;
String currentDirection = "stop";
bool watchdogTripped = false;

void logLine(const String &msg) {
  Serial.println(msg);
  DebugUART.println(msg);
}

const char PAGE_HTML[] PROGMEM = R"HTML(
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sumo Car</title>
<style>
  body { font-family: sans-serif; text-align: center; background:#111; color:#eee; padding: 20px; }
  button { font-size: 1.2em; padding: 12px 24px; border-radius: 8px; border: none; background:#2a7; color:#fff; }
  #status { margin-top: 20px; font-size: 1.1em; }
  #dir { font-size: 2em; font-weight: bold; margin-top: 10px; }
</style>
</head>
<body>
  <h2>Sumo Car - Control por inclinacion</h2>
  <button id="activateBtn">Activar sensores</button>
  <div id="status">Esperando permiso...</div>
  <div id="dir">--</div>
<script>
var activateBtn = document.getElementById('activateBtn');
var statusEl = document.getElementById('status');
var dirEl = document.getElementById('dir');
var lastPitch = 0, lastRoll = 0;
var sending = false;

function onOrientation(event) {
  lastPitch = event.beta || 0;   // front/back tilt
  lastRoll = event.gamma || 0;   // left/right tilt
  statusEl.textContent = 'pitch=' + lastPitch.toFixed(1) + ' roll=' + lastRoll.toFixed(1);
}

function sendTilt() {
  if (sending) return;
  sending = true;
  fetch('/tilt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'pitch=' + lastPitch.toFixed(2) + '&roll=' + lastRoll.toFixed(2)
  }).then(function(res) { return res.text(); })
    .then(function(text) { dirEl.textContent = text; })
    .catch(function() {})
    .finally(function() { sending = false; });
}

function startListening() {
  window.addEventListener('deviceorientation', onOrientation);
  setInterval(sendTilt, 200);
  statusEl.textContent = 'Sensores activos';
}

activateBtn.addEventListener('click', function() {
  if (typeof DeviceOrientationEvent !== 'undefined' &&
      typeof DeviceOrientationEvent.requestPermission === 'function') {
    // iOS 13+: must be requested from a user gesture.
    DeviceOrientationEvent.requestPermission().then(function(permissionState) {
      if (permissionState === 'granted') {
        startListening();
      } else {
        statusEl.textContent = 'Permiso denegado';
      }
    }).catch(function(err) {
      statusEl.textContent = 'Error pidiendo permiso: ' + err;
    });
  } else {
    // Android / other browsers: no explicit permission step needed.
    startListening();
  }
});
</script>
</body>
</html>
)HTML";

void handleRoot() {
  server.send(200, "text/html", PAGE_HTML);
}

String resolveDirection(float pitch, float roll) {
  if (fabs(pitch) < DEADZONE_DEG && fabs(roll) < DEADZONE_DEG) {
    return "stop";
  }
  if (fabs(pitch) >= fabs(roll)) {
    if (fabs(pitch) < THRESHOLD_DEG) return "stop";
    // Measured empirically on this phone: beta > 0 corresponds to tilting
    // backward, not forward -- sign flipped from the original assumption.
    return (pitch > 0) ? "backward" : "forward";
  } else {
    if (fabs(roll) < THRESHOLD_DEG) return "stop";
    return (roll > 0) ? "right" : "left";
  }
}

void handleTiltPost() {
  if (!server.hasArg("pitch") || !server.hasArg("roll")) {
    server.send(400, "text/plain", "missing pitch/roll");
    return;
  }
  lastPitch = server.arg("pitch").toFloat();
  lastRoll = server.arg("roll").toFloat();
  lastTiltMs = millis();
  watchdogTripped = false;

  currentDirection = resolveDirection(lastPitch, lastRoll);

  logLine(String("[tilt] pitch=") + lastPitch + " roll=" + lastRoll +
          " -> direction=" + currentDirection);

  server.send(200, "text/plain", currentDirection);
}

void handleTiltGet() {
  String json = "{\"pitch\":" + String(lastPitch, 2) +
                ",\"roll\":" + String(lastRoll, 2) +
                ",\"direction\":\"" + currentDirection + "\"}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  DebugUART.begin(DEBUG_UART_BAUD, SERIAL_8N1, DEBUG_UART_RX_PIN, DEBUG_UART_TX_PIN);
  delay(1000);
  logLine("");
  logLine("[webserver_tilt] Test sketch starting...");

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  logLine(String("[webserver_tilt] AP SSID=") + AP_SSID + " IP=" + WiFi.softAPIP().toString());

  server.on("/", HTTP_GET, handleRoot);
  server.on("/tilt", HTTP_POST, handleTiltPost);
  server.on("/tilt", HTTP_GET, handleTiltGet);
  server.begin();
  logLine("[webserver_tilt] HTTP server started on port 80.");

  lastTiltMs = millis();
}

void loop() {
  server.handleClient();

  if (!watchdogTripped && millis() - lastTiltMs > WATCHDOG_MS) {
    watchdogTripped = true;
    currentDirection = "stop";
    logLine("[webserver_tilt] WATCHDOG: no fresh /tilt data, forcing stop.");
  }
}
