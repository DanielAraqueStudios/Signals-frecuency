/*
 * SUMO_CAR_PLATFORM - final integrated sketch.
 *
 * ESP32 as WiFi Access Point + embedded HTTP server (WebServer.h) +
 * phone-tilt direction resolution + L298N H-bridge control. No PC, no
 * Python server participates at runtime -- the ESP32 serves its own
 * control page and the phone is just the browser client.
 *
 * Combines:
 *   - sprits/test_wifi_ap        (AP bring-up)
 *   - sprits/test_webserver_tilt (HTTP server + tilt capture + resolveDirection)
 *   - sprits/test_motor_l298n    (L298N motor control)
 *
 * Extras on top of the base Sprint 5 integration:
 *   - Live PWM speed control from the web page (GET/POST /speed, /status).
 *   - On-page control log panel fed by an in-memory ring buffer (/logs).
 *   - Open-loop dead-reckoning minimap (no encoders/GPS -- see notes below).
 *
 * Board: ESP32-S3 (e.g. ESP32-S3-DevKitC-1).
 *
 * Open Serial Monitor at 115200 baud, then connect your phone to the
 * SumoCar WiFi network and browse to http://192.168.4.1/
 *
 * Diagnostic logs are mirrored to both the USB-CDC Serial Monitor and a
 * dedicated hardware UART (DebugUART), so they can also be read from an
 * external USB-TTL adapter independent of the USB-CDC port.
 *
 * See README.md for pin wiring, flashing instructions, and test steps.
 */

#include <WiFi.h>
#include <WebServer.h>

#define AP_SSID "SumoCar"
#define AP_PASSWORD "sumo1234"

// L298N pins (ADJUST to your actual wiring). Chosen in the GPIO 1-21
// range to stay clear of ESP32-S3 strapping pins (0, 3, 45, 46), the
// pins reserved for integrated flash/PSRAM (commonly 26-37), and the
// native USB pins (19/20) on boards that expose USB-OTG.
// L298N wiring (ESP32-S3 GPIO -> L298N input pin):
//   IN1_PIN -> IN1, IN2_PIN -> IN2  (left motor / channel A direction)
//   IN3_PIN -> IN3, IN4_PIN -> IN4  (right motor / channel B direction)
//   ENA_PIN -> ENA (PWM, left motor speed), ENB_PIN -> ENB (PWM, right motor speed)
// Direction truth table per channel (e.g. left motor via IN1/IN2):
//   IN1=HIGH, IN2=LOW  -> spins forward
//   IN1=LOW,  IN2=HIGH -> spins backward
//   IN1=LOW,  IN2=LOW  -> coasts (motor disconnected, free spin)
//   IN1=HIGH, IN2=HIGH -> brakes (both terminals shorted) -- avoid, not used here
// ENA/ENB must also be HIGH (or a nonzero PWM value) for that channel to
// actually drive the motor; 0 on ENA/ENB stops it regardless of IN1/IN2.
#define IN1_PIN 4   // left motor direction pin A (-> L298N IN1)
#define IN2_PIN 5   // left motor direction pin B (-> L298N IN2)
#define IN3_PIN 6   // right motor direction pin A (-> L298N IN3)
#define IN4_PIN 7   // right motor direction pin B (-> L298N IN4)
#define ENA_PIN 15  // left motor speed, PWM (-> L298N ENA)
#define ENB_PIN 16  // right motor speed, PWM (-> L298N ENB)
#define MOTOR_SPEED_DEFAULT 200  // default PWM (0-255), mutable at runtime via /speed

// Direction resolution tuning (degrees).
#define DEADZONE_DEG 8.0
#define THRESHOLD_DEG 15.0

// If no fresh /tilt POST arrives within this window, force "stop".
#define WATCHDOG_MS 800

// Dedicated hardware UART for debug logging only. Pins chosen within the
// safe GPIO 1-21 range, clear of the L298N pins above and of
// strapping/flash-PSRAM/native-USB pins.
#define DEBUG_UART_TX_PIN 17
#define DEBUG_UART_RX_PIN 18
#define DEBUG_UART_BAUD 115200
HardwareSerial DebugUART(1);

// Dead-reckoning calibration constants (OPEN-LOOP ESTIMATE ONLY -- there
// are no encoders/GPS on this car, so posX/posY/headingDeg below WILL
// drift and accumulate error over time. They're a rough on-screen
// reference for the operator, not a real position fix).
// Calibrate LINEAR_SPEED_PER_PWM_UNIT by driving forward at a fixed PWM
// for N seconds, measuring the real distance traveled, and solving
// speed_m_s = distance_m / N; then LINEAR_SPEED_PER_PWM_UNIT = speed_m_s / pwm.
#define LINEAR_SPEED_PER_PWM_UNIT 0.0025  // meters/sec per PWM unit (0-255) -- CALIBRATE on real hardware
// Calibrate ANGULAR_SPEED_PER_PWM_UNIT the same way using the in-place
// spin (motorLeft/motorRight): time a known rotation (e.g. 360 deg) at a
// fixed PWM and solve deg_s = 360 / seconds_for_one_turn; then
// ANGULAR_SPEED_PER_PWM_UNIT = deg_s / pwm.
#define ANGULAR_SPEED_PER_PWM_UNIT 0.35   // degrees/sec per PWM unit -- CALIBRATE on real hardware

// Ring buffer of recent control events (direction/speed changes), shown
// in the on-page logs panel via GET /logs. Fixed-size array -- no
// dynamic heap allocation.
#define CONTROL_LOG_SIZE 20
String controlLogRing[CONTROL_LOG_SIZE];
int controlLogHead = 0;   // next write index
int controlLogCount = 0;  // how many entries are valid (caps at CONTROL_LOG_SIZE)

WebServer server(80);

float lastPitch = 0;
float lastRoll = 0;
unsigned long lastTiltMs = 0;
String currentDirection = "stop";
String appliedDirection = "stop";
int motorSpeed = MOTOR_SPEED_DEFAULT;  // mutable, settable via POST /speed
int appliedSpeed = 0;
bool watchdogTripped = false;

// Dead-reckoning state (see calibration constants above).
float posX = 0;
float posY = 0;
float headingDeg = 0;
unsigned long lastPositionUpdateMs = 0;

void logLine(const String &msg) {
  Serial.println(msg);
  DebugUART.println(msg);
}

void addControlLog(const String &msg) {
  logLine(msg);
  controlLogRing[controlLogHead] = msg;
  controlLogHead = (controlLogHead + 1) % CONTROL_LOG_SIZE;
  if (controlLogCount < CONTROL_LOG_SIZE) controlLogCount++;
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
  button { font-size: 1.1em; padding: 10px 20px; border-radius: 8px; border: none; background:#2a7; color:#fff; margin: 4px; }
  #status { margin-top: 20px; font-size: 1.1em; }
  #dir { font-size: 2em; font-weight: bold; margin-top: 10px; }
  .panel { margin-top: 20px; text-align: left; display: inline-block; }
  #speedInput { width: 220px; }
  #logs { background:#000; color:#9f9; font-family: monospace; font-size: 0.75em; height: 160px; width: 300px; overflow-y: auto; text-align: left; padding: 8px; border-radius: 6px; white-space: pre-wrap; }
  #minimap { background:#000; border-radius: 6px; margin-top: 10px; }
  .note { font-size: 0.8em; color:#999; max-width: 320px; margin: 6px auto; }
</style>
</head>
<body>
  <h2>Sumo Car - Control por inclinacion</h2>
  <button id="activateBtn">Activar sensores</button>
  <div id="status">Esperando permiso...</div>
  <div id="dir">--</div>

  <div class="panel">
    <label for="speedInput">Velocidad PWM (<span id="speedValue">200</span>)</label><br>
    <input type="range" id="speedInput" min="0" max="255" value="200">
  </div>

  <div class="panel">
    <div>Logs de control:</div>
    <div id="logs"></div>
  </div>

  <div class="panel">
    <div>Minimapa (dead-reckoning)</div>
    <canvas id="minimap" width="300" height="300"></canvas><br>
    <button id="resetMapBtn">Reset mapa</button>
  </div>
  <div class="note">
    El minimapa es una estimacion aproximada por dead-reckoning (integracion
    de PWM x tiempo), SIN sensores de posicion real (no hay GPS ni
    encoders). Acumula error con el tiempo -- usalo solo como referencia
    visual de la trayectoria reciente, no como ubicacion precisa.
  </div>

<script>
var activateBtn = document.getElementById('activateBtn');
var statusEl = document.getElementById('status');
var dirEl = document.getElementById('dir');
var speedInput = document.getElementById('speedInput');
var speedValueEl = document.getElementById('speedValue');
var logsEl = document.getElementById('logs');
var resetMapBtn = document.getElementById('resetMapBtn');
var canvas = document.getElementById('minimap');
var ctx = canvas.getContext('2d');
var lastPitch = 0, lastRoll = 0;
var sending = false;
var speedSending = false;
var PIXELS_PER_UNIT = 40;  // minimap scale: 1 posX/posY unit (meter, approx) = 40 px
var lastDrawn = null;

function onOrientation(event) {
  lastPitch = event.beta || 0;
  lastRoll = event.gamma || 0;
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
    startListening();
  }
});

function sendSpeed(value) {
  if (speedSending) return;
  speedSending = true;
  fetch('/speed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'speed=' + value
  }).catch(function() {}).finally(function() { speedSending = false; });
}

speedInput.addEventListener('input', function() {
  speedValueEl.textContent = speedInput.value;
  sendSpeed(speedInput.value);
});

function pollLogs() {
  fetch('/logs').then(function(res) { return res.json(); })
    .then(function(lines) {
      logsEl.textContent = lines.join('\n');
      logsEl.scrollTop = logsEl.scrollHeight;
    }).catch(function() {});
}
setInterval(pollLogs, 1000);

function drawPoint(posX, posY) {
  var cx = canvas.width / 2 + posX * PIXELS_PER_UNIT;
  var cy = canvas.height / 2 - posY * PIXELS_PER_UNIT;
  if (lastDrawn) {
    ctx.strokeStyle = '#2a7';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(lastDrawn.x, lastDrawn.y);
    ctx.lineTo(cx, cy);
    ctx.stroke();
  }
  lastDrawn = { x: cx, y: cy };
}

function pollStatus() {
  fetch('/status').then(function(res) { return res.json(); })
    .then(function(s) {
      drawPoint(s.posX, s.posY);
    }).catch(function() {});
}
setInterval(pollStatus, 300);

function syncSpeedFromStatus() {
  fetch('/status').then(function(res) { return res.json(); })
    .then(function(s) {
      speedInput.value = s.pwm;
      speedValueEl.textContent = s.pwm;
    }).catch(function() {});
}

function clearMap() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#555';
  ctx.beginPath();
  ctx.arc(canvas.width / 2, canvas.height / 2, 4, 0, 2 * Math.PI);
  ctx.fill();
  lastDrawn = { x: canvas.width / 2, y: canvas.height / 2 };
}

resetMapBtn.addEventListener('click', function() {
  fetch('/reset-position', { method: 'POST' }).catch(function() {});
  clearMap();
});

clearMap();
syncSpeedFromStatus();
</script>
</body>
</html>
)HTML";

void setLeftMotor(bool forward, bool reverse, int speed) {
  // Left motor is mounted mirrored relative to the right motor (common on
  // a differential-drive chassis), so IN1/IN2 are swapped here to make
  // "forward"/"reverse" match physical direction, not wiring polarity.
  digitalWrite(IN1_PIN, reverse ? HIGH : LOW);
  digitalWrite(IN2_PIN, forward ? HIGH : LOW);
  analogWrite(ENA_PIN, speed);
}

void setRightMotor(bool forward, bool reverse, int speed) {
  digitalWrite(IN3_PIN, forward ? HIGH : LOW);
  digitalWrite(IN4_PIN, reverse ? HIGH : LOW);
  analogWrite(ENB_PIN, speed);
}

void motorStop() {
  setLeftMotor(false, false, 0);
  setRightMotor(false, false, 0);
}

void motorForward(int speed) {
  setLeftMotor(true, false, speed);
  setRightMotor(true, false, speed);
}

void motorBackward(int speed) {
  setLeftMotor(false, true, speed);
  setRightMotor(false, true, speed);
}

void motorLeft(int speed) {
  setLeftMotor(false, true, speed);
  setRightMotor(true, false, speed);
}

void motorRight(int speed) {
  setLeftMotor(true, false, speed);
  setRightMotor(false, true, speed);
}

void applyDirection(const String &direction) {
  // Re-apply whenever the resolved direction OR the requested PWM speed
  // changed -- a speed-only change (from /speed) while already moving
  // must still reach the motors and get logged.
  if (direction == appliedDirection && motorSpeed == appliedSpeed) return;
  appliedDirection = direction;
  appliedSpeed = motorSpeed;

  if (direction == "forward") {
    motorForward(motorSpeed);
  } else if (direction == "backward") {
    motorBackward(motorSpeed);
  } else if (direction == "left") {
    motorLeft(motorSpeed);
  } else if (direction == "right") {
    motorRight(motorSpeed);
  } else {
    motorStop();
  }

  addControlLog(String("[sumo_car] applyDirection() -> direction=") + direction +
                " pwm=" + motorSpeed + " t=" + millis());
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

void resetPosition() {
  posX = 0;
  posY = 0;
  headingDeg = 0;
  lastPositionUpdateMs = millis();
  addControlLog("[sumo_car] resetPosition() -> posX=0 posY=0 headingDeg=0");
}

// Open-loop dead-reckoning integration step. Called once per loop()
// iteration. Uses appliedDirection/appliedSpeed (what's actually being
// sent to the motors right now), not the raw tilt-resolved direction, so
// the estimate tracks what the car is really doing.
void updatePosition() {
  unsigned long now = millis();
  float dtSec = (now - lastPositionUpdateMs) / 1000.0;
  lastPositionUpdateMs = now;
  if (dtSec <= 0) return;

  if (appliedDirection == "forward" || appliedDirection == "backward") {
    float linearSpeed = appliedSpeed * LINEAR_SPEED_PER_PWM_UNIT;  // meters/sec
    float sign = (appliedDirection == "forward") ? 1.0 : -1.0;
    float headingRad = headingDeg * PI / 180.0;
    posX += sign * linearSpeed * dtSec * cos(headingRad);
    posY += sign * linearSpeed * dtSec * sin(headingRad);
  } else if (appliedDirection == "left" || appliedDirection == "right") {
    float angularSpeed = appliedSpeed * ANGULAR_SPEED_PER_PWM_UNIT;  // degrees/sec
    float sign = (appliedDirection == "right") ? 1.0 : -1.0;
    headingDeg += sign * angularSpeed * dtSec;
    while (headingDeg >= 360.0) headingDeg -= 360.0;
    while (headingDeg < 0.0) headingDeg += 360.0;
  }
  // "stop": position and heading are unchanged.
}

void handleRoot() {
  server.send(200, "text/html", PAGE_HTML);
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
  applyDirection(currentDirection);

  server.send(200, "text/plain", currentDirection);
}

void handleTiltGet() {
  String json = "{\"pitch\":" + String(lastPitch, 2) +
                ",\"roll\":" + String(lastRoll, 2) +
                ",\"direction\":\"" + currentDirection + "\"}";
  server.send(200, "application/json", json);
}

void handleSpeedPost() {
  if (!server.hasArg("speed")) {
    server.send(400, "text/plain", "missing speed");
    return;
  }
  int requested = server.arg("speed").toInt();
  motorSpeed = constrain(requested, 0, 255);
  applyDirection(currentDirection);  // push new PWM to motors immediately if already moving
  server.send(200, "text/plain", String(motorSpeed));
}

void handleLogsGet() {
  String json = "[";
  int startIdx = (controlLogCount < CONTROL_LOG_SIZE) ? 0 : controlLogHead;
  for (int i = 0; i < controlLogCount; i++) {
    int idx = (startIdx + i) % CONTROL_LOG_SIZE;
    if (i > 0) json += ",";
    String escaped = controlLogRing[idx];
    escaped.replace("\\", "\\\\");
    escaped.replace("\"", "\\\"");
    json += "\"" + escaped + "\"";
  }
  json += "]";
  server.send(200, "application/json", json);
}

void handleStatusGet() {
  String json = "{";
  json += "\"pitch\":" + String(lastPitch, 2) + ",";
  json += "\"roll\":" + String(lastRoll, 2) + ",";
  json += "\"direction\":\"" + currentDirection + "\",";
  json += "\"pwm\":" + String(motorSpeed) + ",";
  json += "\"posX\":" + String(posX, 3) + ",";
  json += "\"posY\":" + String(posY, 3) + ",";
  json += "\"headingDeg\":" + String(headingDeg, 1) + ",";
  json += "\"uptimeMs\":" + String(millis());
  json += "}";
  server.send(200, "application/json", json);
}

void handleResetPositionPost() {
  resetPosition();
  server.send(200, "text/plain", "ok");
}

void setup() {
  Serial.begin(115200);
  DebugUART.begin(DEBUG_UART_BAUD, SERIAL_8N1, DEBUG_UART_RX_PIN, DEBUG_UART_TX_PIN);
  delay(1000);
  logLine("");
  logLine("[sumo_car] Starting...");

  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  pinMode(IN3_PIN, OUTPUT);
  pinMode(IN4_PIN, OUTPUT);
  pinMode(ENA_PIN, OUTPUT);
  pinMode(ENB_PIN, OUTPUT);
  motorStop();

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  logLine(String("[sumo_car] AP SSID=") + AP_SSID + " IP=" + WiFi.softAPIP().toString());

  server.on("/", HTTP_GET, handleRoot);
  server.on("/tilt", HTTP_POST, handleTiltPost);
  server.on("/tilt", HTTP_GET, handleTiltGet);
  server.on("/speed", HTTP_POST, handleSpeedPost);
  server.on("/logs", HTTP_GET, handleLogsGet);
  server.on("/status", HTTP_GET, handleStatusGet);
  server.on("/reset-position", HTTP_POST, handleResetPositionPost);
  server.begin();
  logLine("[sumo_car] HTTP server started on port 80.");

  lastTiltMs = millis();
  lastPositionUpdateMs = millis();
}

void loop() {
  server.handleClient();
  updatePosition();

  if (!watchdogTripped && millis() - lastTiltMs > WATCHDOG_MS) {
    watchdogTripped = true;
    currentDirection = "stop";
    applyDirection("stop");
    logLine("[sumo_car] WATCHDOG: no fresh /tilt data, forcing stop.");
  }
}
