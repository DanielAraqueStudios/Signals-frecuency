/*
 * Standalone bring-up sketch: WiFi + local-server reachability + band
 * motor, with NO fingerprint and NO LCD. The band runs continuously
 * (no fingerprint gate needed for this test) and matches the motor to
 * whatever LEVEL /band/pause-status reports -- stays stopped as long as
 * paused=true, resumes the moment it's false (no fixed timer). Same
 * network-trigger logic as the main sketch, isolated here so you can
 * verify the full camera-upload -> pause -> resume loop end-to-end
 * without needing the fingerprint sensor or LCD wired up.
 *
 * Board: ESP32-WROOM-32. Same WiFi credential flow as the main sketch
 * (NVS-stored, entered over Serial on first boot). Same BTS7960 pins as
 * the main sketch: RPWM=25, LPWM=26, EN=27.
 *
 * Open Serial Monitor at 115200 baud, line ending "Newline".
 *
 * Serial commands:
 *   c   -> re-enter and save new SSID/password, then reconnect
 *   i   -> print current connection info (SSID, IP, RSSI)
 *   p   -> poll /band/pause-status once, right now
 *   g   -> poll /images/latest once, right now
 *   o   -> toggle the band on/off manually
 *   +/- -> increase/decrease band motor speed
 */

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <WiFi.h>

// ---------------------------------------------------------------------
// BTS7960 H-bridge (band motor, one direction only) -- same pins as the
// main sketch and test_motor.ino, so wiring carries over unchanged.
// ---------------------------------------------------------------------
#define RPWM_PIN 25
#define LPWM_PIN 26
#define EN_PIN   27
int motorSpeed = 200;   // 0-255
bool motorOn = true;    // runs by default -- no fingerprint gate in this test
bool wasNetworkPaused = false;  // tracks last-applied pause level, to only act on transitions

void applyMotor() {
  if (motorOn) {
    digitalWrite(EN_PIN, HIGH);
    analogWrite(LPWM_PIN, 0);
    analogWrite(RPWM_PIN, motorSpeed);
  } else {
    analogWrite(RPWM_PIN, 0);
    analogWrite(LPWM_PIN, 0);
    digitalWrite(EN_PIN, LOW);
  }
}

// ---------------------------------------------------------------------
// EDIT THIS to match your local-server machine's IP (see
// ../../../scripts/check_network.py on the computer side).
// ---------------------------------------------------------------------
#define LOCAL_SERVER_HOST "10.137.51.134"
#define LOCAL_SERVER_PORT 8100

#define WIFI_SSID_MAX_LEN 32
#define WIFI_PASSWORD_MAX_LEN 64

Preferences wifiPrefs;
char wifiSsid[WIFI_SSID_MAX_LEN + 1];
char wifiPassword[WIFI_PASSWORD_MAX_LEN + 1];

unsigned long lastPollMs = 0;
const unsigned long POLL_INTERVAL_MS = 3000;

// The pause/resume check is polled much more often than classification --
// it's the thing the user is waiting on when they tap a button, so it
// gets its own short interval instead of sharing POLL_INTERVAL_MS.
unsigned long lastPausePollMs = 0;
const unsigned long PAUSE_POLL_INTERVAL_MS = 500;

bool readLineFromSerial(char *outBuf, size_t maxLen, unsigned long timeoutMs) {
  size_t len = 0;
  outBuf[0] = '\0';
  unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    if (Serial.available()) {
      char c = (char)Serial.read();
      if (c == '\n' || c == '\r') {
        if (len > 0) {
          outBuf[len] = '\0';
          return true;
        }
        continue;
      }
      if (len < maxLen - 1) outBuf[len++] = c;
      start = millis();
    }
  }
  outBuf[len] = '\0';
  return len > 0;
}

bool loadWifiCredentials() {
  wifiPrefs.begin("wifi", /*readOnly=*/true);
  size_t ssidLen = wifiPrefs.getString("ssid", wifiSsid, sizeof(wifiSsid));
  wifiPrefs.getString("password", wifiPassword, sizeof(wifiPassword));
  wifiPrefs.end();
  return ssidLen > 0;
}

void saveWifiCredentials(const char *ssid, const char *password) {
  wifiPrefs.begin("wifi", /*readOnly=*/false);
  wifiPrefs.putString("ssid", ssid);
  wifiPrefs.putString("password", password);
  wifiPrefs.end();
}

void promptAndSaveWifiCredentials() {
  Serial.println("[net] Enter WiFi SSID:");
  if (!readLineFromSerial(wifiSsid, sizeof(wifiSsid), 60000UL)) {
    Serial.println("[net] ERROR: no SSID entered (60s timeout).");
    return;
  }
  Serial.println("[net] Enter WiFi password:");
  readLineFromSerial(wifiPassword, sizeof(wifiPassword), 60000UL);
  saveWifiCredentials(wifiSsid, wifiPassword);
}

void connectWiFi() {
  Serial.print("[net] Connecting to SSID='");
  Serial.print(wifiSsid);
  Serial.println("'...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSsid, wifiPassword);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - start > 30000) {
      Serial.println();
      Serial.print("[net] Still not connected after 30s, status=");
      Serial.println(WiFi.status());
      start = millis();
    }
  }
  Serial.println();
  Serial.print("[net] Connected. This ESP32's IP=");
  Serial.print(WiFi.localIP());
  Serial.print(" Gateway (phone)=");
  Serial.println(WiFi.gatewayIP());
  Serial.print("[net] local-server target: http://");
  Serial.print(LOCAL_SERVER_HOST);
  Serial.print(":");
  Serial.println(LOCAL_SERVER_PORT);
}

void printInfo() {
  Serial.print("[net] SSID=");
  Serial.print(WiFi.SSID());
  Serial.print(" IP=");
  Serial.print(WiFi.localIP());
  Serial.print(" RSSI=");
  Serial.println(WiFi.RSSI());
}

// Returns true on a successful HTTP 200. Prints the raw JSON either way.
bool httpGetAndPrint(const char *path) {
  HTTPClient http;
  String url = String("http://") + LOCAL_SERVER_HOST + ":" + LOCAL_SERVER_PORT + path;
  Serial.print("[net] GET ");
  Serial.println(url);
  http.begin(url);
  http.setTimeout(3000);  // never block loop() indefinitely if local-server is down/restarting

  int httpCode = http.GET();
  Serial.print("[net]   HTTP status: ");
  Serial.println(httpCode);
  if (httpCode == 200) {
    String payload = http.getString();
    Serial.print("[net]   Body: ");
    Serial.println(payload);
  } else {
    Serial.println("[net]   FAILED -- check LOCAL_SERVER_HOST/PORT and that local-server is running.");
  }
  http.end();
  return httpCode == 200;
}

// Polls /band/pause-status and matches the motor to whatever LEVEL it
// reports -- stays stopped as long as paused=true, resumes the instant
// it's false. Only acts on an actual transition, not every poll.
void pollPauseStatus() {
  HTTPClient http;
  String url = String("http://") + LOCAL_SERVER_HOST + ":" + LOCAL_SERVER_PORT + "/band/pause-status";
  http.begin(url);
  http.setTimeout(3000);  // never block loop() indefinitely if local-server is down/restarting

  int httpCode = http.GET();
  Serial.print("[net] GET /band/pause-status -> HTTP ");
  Serial.println(httpCode);
  if (httpCode != 200) {
    Serial.println("[net]   FAILED -- check LOCAL_SERVER_HOST/PORT and that local-server is running.");
    http.end();
    return;
  }

  String payload = http.getString();
  Serial.print("[net]   Body: ");
  Serial.println(payload);
  http.end();

  StaticJsonDocument<128> doc;
  if (deserializeJson(doc, payload) != DeserializationError::Ok) {
    Serial.println("[net]   WARN: JSON parse failed");
    return;
  }

  bool paused = doc["pause_requested"] | false;
  if (!motorOn) return;
  bool isTransition = paused != wasNetworkPaused;
  wasNetworkPaused = paused;

  if (paused) {
    // Logs every poll while paused (not just on the transition), so you
    // can see on Serial that it's still alive and genuinely waiting for
    // /band/resume -- not frozen/stuck.
    Serial.println("[motor] Pausa solicitada por detenido. Banda para foto...");
    if (isTransition) {
      analogWrite(RPWM_PIN, 0);
      analogWrite(LPWM_PIN, 0);
      digitalWrite(EN_PIN, LOW);
    }
  } else if (isTransition) {
    Serial.println("[motor] Resumed over network -- running band again.");
    applyMotor();
  }
}

void pollLatestImageResult() {
  httpGetAndPrint("/images/latest");
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("[net] Camera/network test sketch starting (no fingerprint, no LCD; band motor runs by default)...");

  pinMode(RPWM_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  applyMotor();  // starts running (motorOn = true)

  bool haveStoredCreds = loadWifiCredentials();
  if (!haveStoredCreds) {
    Serial.println("[net] No WiFi credentials stored yet.");
    promptAndSaveWifiCredentials();
  } else {
    Serial.print("[net] Stored SSID: ");
    Serial.println(wifiSsid);
    Serial.println("[net] Send 'c' within 5s to change network, or wait to connect...");
    char choice[2];
    if (readLineFromSerial(choice, sizeof(choice), 5000UL) && choice[0] == 'c') {
      promptAndSaveWifiCredentials();
    }
  }

  connectWiFi();
  Serial.println("[net] Will auto-poll /band/pause-status and /images/latest every 3s.");
  Serial.println("[net] Commands: c=change network, i=connection info, p=poll pause-status now, g=poll images/latest now, o=toggle motor, +/-=speed");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[net] WiFi lost, reconnecting...");
    connectWiFi();
  }

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    line.toLowerCase();
    if (line == "c") {
      promptAndSaveWifiCredentials();
      connectWiFi();
    } else if (line == "i") {
      printInfo();
    } else if (line == "p") {
      pollPauseStatus();
    } else if (line == "g") {
      pollLatestImageResult();
    } else if (line == "o") {
      motorOn = !motorOn;
      applyMotor();
      Serial.print("[motor] motorOn=");
      Serial.println(motorOn ? "true" : "false");
    } else if (line == "+") {
      motorSpeed = min(255, motorSpeed + 20);
      applyMotor();
      Serial.print("[motor] speed=");
      Serial.println(motorSpeed);
    } else if (line == "-") {
      motorSpeed = max(0, motorSpeed - 20);
      applyMotor();
      Serial.print("[motor] speed=");
      Serial.println(motorSpeed);
    }
  }

  unsigned long now = millis();

  if (now - lastPausePollMs >= PAUSE_POLL_INTERVAL_MS) {
    lastPausePollMs = now;
    pollPauseStatus();
  }

  if (now - lastPollMs >= POLL_INTERVAL_MS) {
    lastPollMs = now;
    Serial.println("----- auto poll (images/latest) -----");
    pollLatestImageResult();
  }

  delay(50);
}
