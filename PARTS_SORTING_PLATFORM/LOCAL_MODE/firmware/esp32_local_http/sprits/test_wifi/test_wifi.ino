/*
 * Standalone bring-up sketch: WiFi connection only (same credential flow
 * as the main esp32_local_http.ino sketch, isolated for testing).
 *
 * Board: ESP32-WROOM-32. Credentials are entered over Serial on first
 * boot and saved to NVS (Preferences) -- not compiled into the binary --
 * so this sketch can be pointed at any 2.4GHz network without reflashing.
 * See ../../README.md "Before flashing".
 *
 * Open Serial Monitor at 115200 baud, line ending "Newline".
 *
 * Serial commands (once connected):
 *   c   -> re-enter and save new SSID/password, then reconnect
 *   i   -> print current connection info (SSID, IP, RSSI)
 */

#include <Preferences.h>
#include <WiFi.h>

#define WIFI_SSID_MAX_LEN 32
#define WIFI_PASSWORD_MAX_LEN 64

Preferences wifiPrefs;
char wifiSsid[WIFI_SSID_MAX_LEN + 1];
char wifiPassword[WIFI_PASSWORD_MAX_LEN + 1];

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
  Serial.print("[wifi] loadWifiCredentials() -> ssidLen=");
  Serial.println(ssidLen);
  return ssidLen > 0;
}

void saveWifiCredentials(const char *ssid, const char *password) {
  wifiPrefs.begin("wifi", /*readOnly=*/false);
  wifiPrefs.putString("ssid", ssid);
  wifiPrefs.putString("password", password);
  wifiPrefs.end();
  Serial.println("[wifi] Credentials saved to NVS.");
}

void promptAndSaveWifiCredentials() {
  Serial.println("[wifi] Enter WiFi SSID:");
  if (!readLineFromSerial(wifiSsid, sizeof(wifiSsid), 60000UL)) {
    Serial.println("[wifi] ERROR: no SSID entered (60s timeout).");
    return;
  }
  Serial.println("[wifi] Enter WiFi password:");
  readLineFromSerial(wifiPassword, sizeof(wifiPassword), 60000UL);
  saveWifiCredentials(wifiSsid, wifiPassword);
}

void connectWiFi() {
  Serial.print("[wifi] Connecting to SSID='");
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
      Serial.print("[wifi] Still not connected after 30s, status=");
      Serial.println(WiFi.status());
      start = millis();  // keep logging every 30s instead of spamming "."
    }
  }
  Serial.println();
  Serial.print("[wifi] Connected. IP=");
  Serial.print(WiFi.localIP());
  Serial.print(" RSSI=");
  Serial.println(WiFi.RSSI());
}

void printInfo() {
  Serial.print("[wifi] SSID=");
  Serial.print(WiFi.SSID());
  Serial.print(" status=");
  Serial.print(WiFi.status());
  Serial.print(" IP=");
  Serial.print(WiFi.localIP());
  Serial.print(" RSSI=");
  Serial.println(WiFi.RSSI());
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("[wifi] Test sketch starting...");

  bool haveStoredCreds = loadWifiCredentials();
  if (!haveStoredCreds) {
    Serial.println("[wifi] No credentials stored yet.");
    promptAndSaveWifiCredentials();
  } else {
    Serial.print("[wifi] Stored SSID: ");
    Serial.println(wifiSsid);
    Serial.println("[wifi] Send 'c' within 5s to change network, or wait to connect...");
    char choice[2];
    if (readLineFromSerial(choice, sizeof(choice), 5000UL) && choice[0] == 'c') {
      promptAndSaveWifiCredentials();
    }
  }

  connectWiFi();
  Serial.println("[wifi] Commands: c=change network, i=connection info");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[wifi] Connection lost, reconnecting...");
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
    }
  }

  delay(50);
}
