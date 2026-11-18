/*
 * PARTS_SORTING_PLATFORM - LOCAL_MODE ESP32 band controller + result display
 *
 * Local-mode counterpart to
 * ../../../CLOUD_MODE/firmware/esp32s3_result_display/esp32s3_result_display.ino.
 * Same WiFi/HTTP-poll job (connect to WiFi, poll local-server for a
 * classification result) plus the actual band hardware control:
 *
 *   - Fingerprint sensor (Adafruit_Fingerprint) gates the band motor:
 *     a recognized fingerprint toggles the motor on/off. An unrecognized
 *     fingerprint is rejected -- the motor never runs for an unknown user.
 *   - BTS7960 H-bridge drives the band motor (one direction only; this
 *     rig doesn't need reverse).
 *   - Band pause/resume is triggered over the NETWORK instead of by the
 *     VL53L0X distance sensor, which isn't working reliably on this rig.
 *     A second device (an Android phone, fixed IP on the same LAN) has
 *     two on-screen buttons (local-server's static/pause_button.html):
 *     POST /band/pause stops the band, POST /band/resume starts it again.
 *     This sketch polls GET /band/pause-status (alongside its existing
 *     /images/latest poll) and matches the motor to whatever LEVEL that
 *     reports -- see applyNetworkPauseState() below and
 *     ../../local-server/app/pause_trigger.py. Unlike an earlier version
 *     of this mechanism, this is not a timed one-shot: the band stays
 *     stopped for as long as the server reports paused=true. This only
 *     fires while the fingerprint-authorized motorOn is true; it doesn't
 *     change that authorization, just holds the band within it.
 *     The VL53L0X wiring/code is left in sprits/test_distance_sensor/
 *     for whenever the sensor itself is fixed and this can switch back.
 *   - 16x2 I2C LCD replaces the optional SSD1306 OLED block from the
 *     earlier version of this sketch: shows motor state + last fingerprint
 *     ID, and the latest classification result polled from local-server.
 *   - WiFi SSID/password still are NOT baked into the compiled binary:
 *     entered once over Serial and stored in NVS (Preferences), so the
 *     same compiled firmware can be pointed at any WiFi network (any
 *     Android hotspot, any router) without recompiling/reflashing. See
 *     setup()/promptAndSaveWifiCredentials() below.
 *   - Polls LOCAL_MODE/local-server's GET /images/latest on a
 *     millis()-based non-blocking timer instead of subscribing to a
 *     broker topic -- there is no push mechanism in this simple mode.
 *   - Explicitly unsecured: this only makes sense on a closed LAN/demo
 *     access point, never exposed to the internet (see
 *     ../../local-server/README.md).
 *
 * Board: ESP32-WROOM-32 (no PSRAM, so GPIO16/17 are free for the
 * fingerprint sensor's UART2 -- on an ESP32-WROVER those two pins are
 * reserved for PSRAM and this pin assignment would need to change).
 * Board package required: Arduino-ESP32 core **3.x** (same requirement as
 * the cloud-mode sketch and LAB_TESTING/LAB1/firmware).
 *
 * NOT verified on real hardware or compiled with the Arduino IDE /
 * arduino-cli in this environment -- see README.md "What could not be
 * verified".
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_Fingerprint.h>
// Adafruit_VL53L0X.h is no longer used here -- see the pause-for-photo
// note above. Kept in sprits/test_distance_sensor/ for later.

// ---------------------------------------------------------------------
// WiFi credentials are no longer compiled in. On every boot this sketch
// loads SSID/password from NVS (via Preferences, namespace "wifi"); if
// none are stored yet, or if you send 'c' over Serial within the first
// few seconds, it prompts for new ones over Serial and saves them --
// so the same binary works on the Android phone's hotspot (2.4GHz/
// compatibility mode -- most ESP32 boards can't join a 5GHz-only
// hotspot) today and a different network tomorrow, with no reflash.
// See ../../NETWORK_SETUP.md for hotspot setup/IP details and
// promptAndSaveWifiCredentials() below for how to (re)enter credentials.
// ---------------------------------------------------------------------
Preferences wifiPrefs;
#define WIFI_SSID_MAX_LEN 32
#define WIFI_PASSWORD_MAX_LEN 64
char wifiSsid[WIFI_SSID_MAX_LEN + 1];
char wifiPassword[WIFI_PASSWORD_MAX_LEN + 1];

// ---------------------------------------------------------------------
// EDIT THIS: local-server's LAN address. Must be a static/reserved DHCP
// IP -- there is no discovery mechanism in this simple mode. Port must
// match how local-server was started (see ../../local-server/README.md,
// default 8100).
// ---------------------------------------------------------------------
#define LOCAL_SERVER_HOST "10.137.51.134"
#define LOCAL_SERVER_PORT 8100

// ---------------------------------------------------------------------
// LCD (16x2, PCF8574 I2C backpack)
// ---------------------------------------------------------------------
#define LCD_ADDR 0x27
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);

// ---------------------------------------------------------------------
// Fingerprint sensor (UART2). Gates the band motor: a recognized
// fingerprint toggles the motor; an unrecognized one is rejected.
// ---------------------------------------------------------------------
HardwareSerial fingerSerial(2);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&fingerSerial);

// ---------------------------------------------------------------------
// BTS7960 H-bridge (band motor, one direction only)
// ---------------------------------------------------------------------
#define RPWM_PIN 25
#define LPWM_PIN 26
#define EN_PIN   27

int motorSpeed = 200;          // 0-255
bool motorOn = false;
int lastFingerId = 0;          // last fingerprint ID that toggled the motor

bool awaitingEraseAllConfirm = false;

#define MAX_LABELS 16
struct LabelCount {
  char label[24];
  uint32_t count;
};
LabelCount labelCounts[MAX_LABELS];
uint8_t labelCountsUsed = 0;

// Non-blocking poll timing -- same discipline as the cloud-mode sketch's
// reconnect timing (no hardware timer needed; this sketch is I/O-driven).
unsigned long lastPollMs = 0;
const unsigned long POLL_INTERVAL_MS = 3000;

// The pause/resume check is polled much more often than classification --
// it's the thing the user is waiting on when they tap a button, so it
// gets its own short interval instead of sharing POLL_INTERVAL_MS.
unsigned long lastPausePollMs = 0;
const unsigned long PAUSE_POLL_INTERVAL_MS = 500;

// Tracks the last-seen label so we only print/count when the result
// actually changes, instead of once per poll.
char lastSeenLabel[24] = "";

// Last-seen diameter (cm) alongside lastSeenLabel, for showStatusScreen()'s
// LCD line 2. hasDiameter is tracked separately rather than using a
// sentinel on the float here, since showStatusScreen() needs a clean
// boolean to decide whether to alternate in a diameter frame at all.
float lastSeenDiameterCm = -1.0f;
bool lastSeenHasDiameter = false;

// =====================================================
// Serial helpers
// =====================================================

// Blocks waiting for a line (terminated by '\n') from Serial, up to
// timeoutMs, writing at most maxLen-1 bytes into outBuf (always
// NUL-terminated). Returns false on timeout/empty input. Bounded and
// timed out on purpose -- this runs once at boot, never in a hot path.
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
        continue;  // ignore leading newlines
      }
      if (len < maxLen - 1) {
        outBuf[len++] = c;
      }
      start = millis();  // reset timeout while the user is actively typing
    }
  }
  outBuf[len] = '\0';
  return len > 0;
}

// =====================================================
// WiFi
// =====================================================

// Loads WiFi credentials from NVS into wifiSsid/wifiPassword. Returns
// false if nothing is stored yet (first boot, or after a cleared NVS).
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

// Interactively asks for SSID + password over Serial and persists them
// to NVS so every later boot reuses them without asking again. Call
// this once at setup() when no credentials are stored, or when the
// user asks to change network (sends 'c' during the boot prompt).
void promptAndSaveWifiCredentials() {
  Serial.println("Enter WiFi SSID:");
  if (!readLineFromSerial(wifiSsid, sizeof(wifiSsid), 60000UL)) {
    Serial.println("ERROR: no SSID entered (60s timeout), cannot continue");
    while (true) {
      delay(1000);  // halt: nothing useful to do without credentials
    }
  }
  Serial.println("Enter WiFi password:");
  readLineFromSerial(wifiPassword, sizeof(wifiPassword), 60000UL);
  saveWifiCredentials(wifiSsid, wifiPassword);
  Serial.println("WiFi credentials saved to NVS.");
}

void connectWiFi() {
  Serial.print("WiFi: connecting to ");
  Serial.println(wifiSsid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSsid, wifiPassword);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  printNetworkAddresses();
}

// Prints every address relevant to setting this rig up, so you don't have
// to go hunting across devices to know what to type where.
void printNetworkAddresses() {
  Serial.println("===== Network addresses =====");
  Serial.print("This ESP32's own IP:      ");
  Serial.println(WiFi.localIP());
  Serial.print("Hotspot gateway (phone):  ");
  Serial.println(WiFi.gatewayIP());
  Serial.print("local-server configured:  http://");
  Serial.print(LOCAL_SERVER_HOST);
  Serial.print(":");
  Serial.println(LOCAL_SERVER_PORT);
  Serial.println(
      "If LOCAL_SERVER_HOST above doesn't match the actual local-server "
      "machine's IP, edit the #define at the top of this .ino and reflash.");
  Serial.println("==============================");
}

// =====================================================
// LCD
// =====================================================
// LCD layout tradeoff: 16x2, line 1 is already committed to band status
// ("BANDA: ENCENDIDA/APAGADA"), so classification + diameter must share
// line 2's 16 characters. They don't fit together -- "brocas (92%)" is
// already 12 chars, leaving only 4 for a diameter ("D=X" needs more than
// that to be useful) -- so instead of truncating one of them, line 2
// ALTERNATES between a label frame and a diameter frame every
// LCD_FRAME_MS, driven by millis() so no delay()/blocking is needed.
// Only alternates when a diameter is actually available (lastSeenHasDiameter);
// otherwise line 2 just shows the label frame every time. The Serial log
// in pollLatestResult() always has the full, non-truncated detail
// regardless of this LCD simplification.
const unsigned long LCD_FRAME_MS = 2000;

void showStatusScreen() {
  lcd.clear();
  lcd.setCursor(0, 0);
  if (motorOn) lcd.print("BANDA: ENCENDIDA");
  else         lcd.print("BANDA: APAGADA");

  lcd.setCursor(0, 1);
  if (lastSeenLabel[0] != '\0') {
    bool showDiameterFrame =
        lastSeenHasDiameter && ((millis() / LCD_FRAME_MS) % 2 == 1);
    if (showDiameterFrame) {
      char diameterLine[17];
      snprintf(diameterLine, sizeof(diameterLine), "D=%.2fcm", lastSeenDiameterCm);
      lcd.print(diameterLine);
    } else {
      lcd.print(lastSeenLabel);
    }
  } else if (lastFingerId > 0) {
    lcd.print("Huella ID: ");
    lcd.print(lastFingerId);
  } else {
    lcd.print("Ponga su huella");
  }
}

void showMessageScreen(const char *line1, const char *line2, int ms) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
  delay(ms);
}

// =====================================================
// Motor
// =====================================================
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

// =====================================================
// Network pause/resume (band pause for photo)
// =====================================================
// Stands in for the VL53L0X distance sensor, which isn't working
// reliably on this rig. A second device (phone, fixed IP on the same
// LAN) has two buttons: POST /band/pause, POST /band/resume. We poll
// GET /band/pause-status here -- this is a LEVEL, not a one-shot: the
// band stays stopped for as long as the server reports paused=true, and
// resumes the moment it reports false (no fixed delay/timer). Only acts
// while the band is authorized to run (motorOn) -- does not change
// motorOn itself, so the fingerprint-driven authorization is untouched.
bool pollNetworkPauseState() {
  HTTPClient http;
  String url = String("http://") + LOCAL_SERVER_HOST + ":" + LOCAL_SERVER_PORT + "/band/pause-status";
  http.begin(url);
  http.setTimeout(3000);  // never block loop() indefinitely if local-server is down/restarting

  int httpCode = http.GET();
  if (httpCode != 200) {
    Serial.print("WARN: GET /band/pause-status failed, code=");
    Serial.println(httpCode);
    http.end();
    return false;
  }

  String payload = http.getString();
  http.end();

  StaticJsonDocument<128> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.print("WARN: JSON parse failed: ");
    Serial.println(err.c_str());
    return false;
  }

  return doc["pause_requested"] | false;
}

// Tracks whether we last applied the "paused" pin state, so we only
// touch pins (and the LCD) on an actual transition instead of every
// poll cycle.
bool wasNetworkPaused = false;

void applyNetworkPauseState() {
  if (!motorOn) return;
  bool paused = pollNetworkPauseState();
  bool isTransition = paused != wasNetworkPaused;
  wasNetworkPaused = paused;

  if (paused) {
    // Logs on every poll while paused (not just the transition into it),
    // so you can see on Serial that it's still alive and genuinely
    // waiting for /band/resume -- not frozen/stuck.
    Serial.println("Pausa solicitada por detenido. Banda para foto...");
    if (isTransition) {
      analogWrite(RPWM_PIN, 0);
      analogWrite(LPWM_PIN, 0);
      digitalWrite(EN_PIN, LOW);
      showMessageScreen("Pausa (red)", "Tomando foto...", 0);
      showStatusScreen();
    }
  } else if (isTransition) {
    Serial.println("Reanudado por red. Reanudando banda...");
    applyMotor();  // restores to motorOn's state (still true here)
    showStatusScreen();
  }
}

// =====================================================
// Fingerprint
// =====================================================
// 0 = no finger, -1 = not recognized, >0 = recognized ID
int readFingerprint() {
  if (finger.getImage() != FINGERPRINT_OK) return 0;
  if (finger.image2Tz() != FINGERPRINT_OK) return 0;
  if (finger.fingerFastSearch() != FINGERPRINT_OK) return -1;
  return finger.fingerID;
}

uint8_t waitForImage(unsigned long ms) {
  unsigned long t = millis();
  uint8_t p = FINGERPRINT_NOFINGER;
  while (millis() - t < ms) {
    p = finger.getImage();
    if (p == FINGERPRINT_OK) return p;
    delay(30);
  }
  return p;
}

bool enrollFingerprint(uint8_t id) {
  Serial.print("Coloca el dedo para registrar el ID #");
  Serial.println(id);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Registrando ID ");
  lcd.print(id);
  lcd.setCursor(0, 1);
  lcd.print("Ponga el dedo");

  uint8_t p = waitForImage(15000);
  if (p != FINGERPRINT_OK) {
    Serial.println("Tiempo agotado.");
    return false;
  }
  if (finger.image2Tz(1) != FINGERPRINT_OK) {
    Serial.println("Error al procesar la primera imagen.");
    return false;
  }

  Serial.println("Retira el dedo...");
  lcd.setCursor(0, 1);
  lcd.print("Retire el dedo  ");
  delay(1500);
  unsigned long t = millis();
  while (finger.getImage() != FINGERPRINT_NOFINGER) {
    delay(50);
    if (millis() - t > 10000) break;
  }

  Serial.println("Coloca el MISMO dedo otra vez...");
  lcd.setCursor(0, 1);
  lcd.print("Mismo dedo otra ");
  p = waitForImage(15000);
  if (p != FINGERPRINT_OK) {
    Serial.println("Tiempo agotado.");
    return false;
  }
  if (finger.image2Tz(2) != FINGERPRINT_OK) {
    Serial.println("Error al procesar la segunda imagen.");
    return false;
  }
  if (finger.createModel() != FINGERPRINT_OK) {
    Serial.println("Las dos lecturas no coinciden.");
    return false;
  }
  if (finger.storeModel(id) == FINGERPRINT_OK) {
    Serial.print("Huella guardada en ID ");
    Serial.println(id);
    return true;
  }
  Serial.println("Error al guardar en el sensor.");
  return false;
}

void listFingerprints() {
  finger.getTemplateCount();
  Serial.print("Huellas guardadas: ");
  Serial.println(finger.templateCount);
  Serial.print("IDs ocupados: ");
  bool any = false;
  for (int id = 1; id <= 127; id++) {
    if (finger.loadModel(id) == FINGERPRINT_OK) {
      Serial.print(id);
      Serial.print(" ");
      any = true;
    }
  }
  if (!any) Serial.print("(ninguno)");
  Serial.println();
}

int firstFreeFingerId() {
  for (int id = 1; id <= 127; id++) {
    if (finger.loadModel(id) != FINGERPRINT_OK) return id;
  }
  return -1;
}

// =====================================================
// Band / classification result (HTTP poll)
// =====================================================
void bumpLabelCount(const char *label) {
  for (uint8_t i = 0; i < labelCountsUsed; i++) {
    if (strncmp(labelCounts[i].label, label, sizeof(labelCounts[i].label)) == 0) {
      labelCounts[i].count++;
      return;
    }
  }
  if (labelCountsUsed < MAX_LABELS) {
    strncpy(labelCounts[labelCountsUsed].label, label, sizeof(labelCounts[labelCountsUsed].label) - 1);
    labelCounts[labelCountsUsed].label[sizeof(labelCounts[labelCountsUsed].label) - 1] = '\0';
    labelCounts[labelCountsUsed].count = 1;
    labelCountsUsed++;
  } else {
    Serial.println("WARN: label count table full, dropping new label from counts");
  }
}

void printLabelCounts() {
  Serial.println("--- running counts ---");
  for (uint8_t i = 0; i < labelCountsUsed; i++) {
    Serial.print("  ");
    Serial.print(labelCounts[i].label);
    Serial.print(": ");
    Serial.println(labelCounts[i].count);
  }
  Serial.println("-----------------------");
}

void pollLatestResult() {
  HTTPClient http;
  String url = String("http://") + LOCAL_SERVER_HOST + ":" + LOCAL_SERVER_PORT + "/images/latest";
  http.begin(url);
  http.setTimeout(3000);  // never block loop() indefinitely if local-server is down/restarting

  int httpCode = http.GET();
  if (httpCode != 200) {
    Serial.print("WARN: GET /images/latest failed, code=");
    Serial.println(httpCode);
    http.end();
    return;
  }

  String payload = http.getString();
  http.end();

  StaticJsonDocument<512> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.print("WARN: JSON parse failed: ");
    Serial.println(err.c_str());
    return;
  }

  const char *label = doc["label"] | "unknown";
  bool isStub = doc["stub"] | false;
  bool hasConfidence = doc.containsKey("confidence") && !doc["confidence"].isNull();
  float confidence = doc["confidence"] | 0.0f;

  // diameter_cm is a new field from local-server's diameter-measurement
  // module (computed alongside the YOLO label on the same photo); it may
  // be JSON null when the measurement failed or wasn't attempted.
  // ArduinoJson's `| default` operator falls back to default whenever the
  // variant isn't convertible to the requested type -- a JSON null is not
  // convertible to float (JsonVariant::is<float>() returns false for it),
  // so `doc["diameter_cm"] | -1.0f` correctly yields -1.0f for null, same
  // as for a missing key. -1.0f (not 0.0f) is the sentinel for "no
  // diameter available" since 0 would look like a plausible-but-wrong
  // reading.
  float diameterCm = doc["diameter_cm"] | -1.0f;
  bool hasDiameter = diameterCm >= 0.0f;

  // Only act when the result actually changed since the last poll --
  // avoids re-counting the same classification every 3s.
  if (strncmp(lastSeenLabel, label, sizeof(lastSeenLabel)) == 0) {
    return;
  }
  strncpy(lastSeenLabel, label, sizeof(lastSeenLabel) - 1);
  lastSeenLabel[sizeof(lastSeenLabel) - 1] = '\0';

  char line[64];
  if (isStub) {
    snprintf(line, sizeof(line), "STUB: %s", label);
  } else if (hasConfidence) {
    snprintf(line, sizeof(line), "%s (%.0f%%)", label, confidence * 100.0f);
  } else {
    snprintf(line, sizeof(line), "%s", label);
  }
  // Append the diameter to the full (non-LCD-constrained) Serial line
  // when available; omit it entirely when not, rather than printing the
  // -1.00cm sentinel.
  if (hasDiameter) {
    size_t used = strlen(line);
    snprintf(line + used, sizeof(line) - used, " D=%.2fcm", diameterCm);
  }

  Serial.print("Result: ");
  Serial.println(line);

  bumpLabelCount(label);
  printLabelCounts();

  // lastSeenLabel/lastSeenDiameterCm feed showStatusScreen()'s LCD
  // line 2 -- see the alternating-display comment there for why the
  // diameter isn't just appended to the label string.
  lastSeenDiameterCm = diameterCm;
  lastSeenHasDiameter = hasDiameter;

  showStatusScreen();
}

// =====================================================
// Serial menu (fingerprint enrollment + motor speed)
// =====================================================
void printMenu() {
  Serial.println();
  Serial.println("========== MENU ==========");
  Serial.println(" a        -> mostrar menu");
  Serial.println(" l        -> listar IDs ocupados");
  Serial.println(" n        -> registrar en siguiente ID libre");
  Serial.println(" r <id>   -> registrar en ese ID (ej: r 5)");
  Serial.println(" b <id>   -> borrar ese ID (ej: b 5)");
  Serial.println(" vaciar   -> borrar TODAS las huellas");
  Serial.println(" +  /  -  -> velocidad mas rapida / mas lenta");
  Serial.println("==========================");
}

void handleSerialMenu() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();
  line.toLowerCase();
  if (line.length() == 0) return;

  if (awaitingEraseAllConfirm) {
    awaitingEraseAllConfirm = false;
    if (line == "si") {
      if (finger.emptyDatabase() == FINGERPRINT_OK) Serial.println("Todas las huellas borradas.");
      else Serial.println("Error al vaciar.");
    } else {
      Serial.println("Cancelado.");
    }
    return;
  }

  if (line == "a") {
    printMenu();
  } else if (line == "l") {
    listFingerprints();
  } else if (line == "n") {
    int id = firstFreeFingerId();
    if (id == -1) {
      Serial.println("No hay IDs libres.");
    } else {
      enrollFingerprint(id);
      showStatusScreen();
    }
  } else if (line == "vaciar") {
    Serial.println("Seguro? Escribe 'si' para borrar TODAS las huellas.");
    awaitingEraseAllConfirm = true;
  } else if (line.startsWith("r ")) {
    int id = line.substring(2).toInt();
    if (id >= 1 && id <= 127) {
      enrollFingerprint(id);
      showStatusScreen();
    } else {
      Serial.println("ID invalido (1 a 127).");
    }
  } else if (line.startsWith("b ")) {
    int id = line.substring(2).toInt();
    if (id >= 1 && id <= 127) {
      if (finger.deleteModel(id) == FINGERPRINT_OK) {
        Serial.print("Huella ID ");
        Serial.print(id);
        Serial.println(" borrada.");
      } else {
        Serial.println("No se pudo borrar.");
      }
    } else {
      Serial.println("ID invalido (1 a 127).");
    }
  } else if (line == "+") {
    motorSpeed = min(255, motorSpeed + 20);
    applyMotor();
    Serial.print("Velocidad: ");
    Serial.println(motorSpeed);
  } else if (line == "-") {
    motorSpeed = max(0, motorSpeed - 20);
    applyMotor();
    Serial.print("Velocidad: ");
    Serial.println(motorSpeed);
  } else {
    Serial.println("Comando no reconocido. Escribe 'a' para ver el menu.");
  }
}

// =====================================================
// SETUP
// =====================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("ESP32 local-mode band controller starting...");

  pinMode(RPWM_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  applyMotor();  // starts off

  // Fingerprint sensor is initialized BEFORE Wire/LCD on purpose: in
  // testing, initializing the LCD (Wire.begin + lcd.init + backlight)
  // first made finger.verifyPassword() fail here even though the exact
  // same wiring passed every time in the isolated sprits/test_fingerprint
  // sketch (which does nothing but Serial.begin() + fingerprint init).
  // Likely cause: turning on the LCD backlight draws current on the same
  // 3.3V rail right as the sensor is settling after power-up, and a
  // marginal onboard regulator can't hold voltage through both at once.
  // Matching the working test's exact boot order avoids that.
  //
  // Do NOT call finger.begin() -- same note as the original sketch.
  fingerSerial.begin(57600, SERIAL_8N1, 16, 17);
  delay(500);

  if (finger.verifyPassword()) {
    Serial.println("Sensor de huella detectado.");
  } else {
    Serial.println("No se encontro el sensor. Revisa cableado y 3V3.");
    while (true) {
      delay(1000);
    }
  }

  listFingerprints();
  printMenu();

  // No VL53L0X init here -- the pause-for-photo trigger comes from the
  // network poll instead (applyNetworkPauseState() in loop()).
  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();
  showMessageScreen("Iniciando...", "Conectando WiFi", 800);

  bool haveStoredCreds = loadWifiCredentials();
  if (!haveStoredCreds) {
    Serial.println("No WiFi credentials stored yet.");
    promptAndSaveWifiCredentials();
  } else {
    Serial.print("Stored WiFi SSID: ");
    Serial.println(wifiSsid);
    Serial.println("Send 'c' within 5s to change network, or wait to connect...");
    char choice[2];
    if (readLineFromSerial(choice, sizeof(choice), 5000UL) && choice[0] == 'c') {
      promptAndSaveWifiCredentials();
    }
  }

  connectWiFi();
  showStatusScreen();
}

// =====================================================
// LOOP
// =====================================================
void loop() {
  handleSerialMenu();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi: connection lost, reconnecting...");
    connectWiFi();
  }

  unsigned long now = millis();
  if (now - lastPollMs >= POLL_INTERVAL_MS) {
    lastPollMs = now;
    pollLatestResult();
  }

  // Redraws line 2 so the label/diameter alternation (see showStatusScreen()'s
  // LCD layout comment) actually advances over time, not just on the next
  // result change or fingerprint event.
  static unsigned long lastLcdRefreshMs = 0;
  if (lastSeenHasDiameter && now - lastLcdRefreshMs >= LCD_FRAME_MS) {
    lastLcdRefreshMs = now;
    showStatusScreen();
  }

  if (now - lastPausePollMs >= PAUSE_POLL_INTERVAL_MS) {
    lastPausePollMs = now;
    applyNetworkPauseState();
  }

  int fp = readFingerprint();

  if (fp > 0) {
    lastFingerId = fp;
    motorOn = !motorOn;
    applyMotor();

    if (motorOn) {
      Serial.print("Huella ID "); Serial.print(fp); Serial.println(" -> BANDA ENCENDIDA");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Huella ID: ");
      lcd.print(fp);
      lcd.setCursor(0, 1);
      lcd.print("Encendiendo...");
    } else {
      Serial.print("Huella ID "); Serial.print(fp); Serial.println(" -> BANDA APAGADA");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Huella ID: ");
      lcd.print(fp);
      lcd.setCursor(0, 1);
      lcd.print("Apagando...");
    }
    delay(1000);
    showStatusScreen();

    // Wait for the finger to lift so one touch doesn't toggle repeatedly.
    unsigned long t = millis();
    while (finger.getImage() != FINGERPRINT_NOFINGER) {
      delay(50);
      if (millis() - t > 5000) break;
    }
    delay(300);

  } else if (fp == -1) {
    Serial.println("Huella NO reconocida.");
    showMessageScreen("Huella NO", "reconocida", 1200);
    showStatusScreen();
  }

  delay(50);
}
