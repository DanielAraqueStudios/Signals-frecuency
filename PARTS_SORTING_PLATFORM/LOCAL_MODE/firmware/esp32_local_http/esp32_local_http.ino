/*
 * PARTS_SORTING_PLATFORM - LOCAL_MODE ESP32 result display
 *
 * Local-mode counterpart to
 * ../../../CLOUD_MODE/firmware/esp32s3_result_display/esp32s3_result_display.ino.
 * Same board target and job (connect to WiFi, poll for a classification
 * result, print it to Serial/OLED, keep a running per-label count) but:
 *
 *   - No TLS, no MQTT library. Uses HTTPClient for plain HTTP GET.
 *   - Same predefined WiFi SSID/password pattern as the cloud-mode sketch.
 *   - Polls LOCAL_MODE/local-server's GET /images/latest on a
 *     millis()-based non-blocking timer instead of subscribing to a
 *     broker topic -- there is no push mechanism in this simple mode.
 *   - Explicitly unsecured: this only makes sense on a closed LAN/demo
 *     access point, never exposed to the internet (see
 *     ../../local-server/README.md).
 *
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

// ---------------------------------------------------------------------
// EDIT THIS: WiFi credentials -- the same predefined access point the
// phone and the local-server computer are also joined to.
// ---------------------------------------------------------------------
#define WIFI_SSID "EDIT_THIS_WIFI_SSID"
#define WIFI_PASSWORD "EDIT_THIS_WIFI_PASSWORD"

// ---------------------------------------------------------------------
// EDIT THIS: local-server's LAN address. Must be a static/reserved DHCP
// IP -- there is no discovery mechanism in this simple mode. Port must
// match how local-server was started (see ../../local-server/README.md,
// default 8100).
// ---------------------------------------------------------------------
#define LOCAL_SERVER_HOST "EDIT_THIS_192_168_X_X"
#define LOCAL_SERVER_PORT 8100

// ---------------------------------------------------------------------
// Optional OLED (SSD1306 over I2C) -- identical block to the cloud-mode
// sketch. Leave HAS_OLED undefined to run Serial-only.
// ---------------------------------------------------------------------
// #define HAS_OLED

#ifdef HAS_OLED
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#define OLED_WIDTH 128
#define OLED_HEIGHT 64
#define OLED_I2C_ADDRESS 0x3C
Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
#endif

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

// Tracks the last-seen label so we only print/count when the result
// actually changes, instead of once per poll.
char lastSeenLabel[24] = "";

void connectWiFi() {
  Serial.print("WiFi: connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi: connected, IP=");
  Serial.println(WiFi.localIP());
}

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

#ifdef HAS_OLED
void showOnOled(const char *line1, const char *line2) {
  oled.clearDisplay();
  oled.setCursor(0, 0);
  oled.println(line1);
  oled.println(line2);
  oled.display();
}
#endif

void pollLatestResult() {
  HTTPClient http;
  String url = String("http://") + LOCAL_SERVER_HOST + ":" + LOCAL_SERVER_PORT + "/images/latest";
  http.begin(url);

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

  Serial.print("Result: ");
  Serial.println(line);

  bumpLabelCount(label);
  printLabelCounts();

#ifdef HAS_OLED
  showOnOled(line, "count: see Serial");
#endif
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println("ESP32 local-mode result display starting...");

#ifdef HAS_OLED
  Wire.begin();
  if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDRESS)) {
    Serial.println("WARN: SSD1306 OLED not found, continuing Serial-only");
  } else {
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    oled.setCursor(0, 0);
    oled.println("Starting...");
    oled.display();
  }
#endif

  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi: connection lost, reconnecting...");
    connectWiFi();
  }

  unsigned long now = millis();
  if (now - lastPollMs >= POLL_INTERVAL_MS) {
    lastPollMs = now;
    pollLatestResult();
  }
}
