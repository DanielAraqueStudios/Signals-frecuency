/*
 * Standalone bring-up sketch: WiFi Access Point only (Sprint 1).
 *
 * Board: ESP32-S3 (e.g. ESP32-S3-DevKitC-1). The ESP32 creates its own WiFi
 * network with WiFi.softAP() -- no router, no phone hotspot, no PC in
 * the loop. The phone connects directly to this network and will reach
 * the ESP32 at the fixed AP IP (192.168.4.1 by default).
 *
 * No H-bridge, no HTTP server yet -- this sketch only verifies that the
 * AP comes up and that a phone can join it.
 *
 * Logging goes to both the USB-CDC Serial Monitor (115200 baud) and a
 * dedicated hardware UART (DebugUART, also 115200) on DEBUG_UART_TX_PIN/
 * DEBUG_UART_RX_PIN, so logs can also be read with an external USB-TTL
 * adapter, independent of the USB-CDC port.
 */

#include <WiFi.h>

#define AP_SSID "SumoCar"
#define AP_PASSWORD "sumo1234"  // WPA2 requires >= 8 chars

// Dedicated hardware UART for debug logging only (separate from the
// USB-CDC Serial used for interactive commands). Pins chosen within the
// safe GPIO 1-21 range, clear of the L298N pins used elsewhere in this
// project (4,5,6,7,15,16) and of strapping/flash-PSRAM/native-USB pins.
#define DEBUG_UART_TX_PIN 17
#define DEBUG_UART_RX_PIN 18
#define DEBUG_UART_BAUD 115200
HardwareSerial DebugUART(1);

unsigned long lastStatusPrintMs = 0;
#define STATUS_PRINT_INTERVAL_MS 5000

void logLine(const String &msg) {
  Serial.println(msg);
  DebugUART.println(msg);
}

void setup() {
  Serial.begin(115200);
  DebugUART.begin(DEBUG_UART_BAUD, SERIAL_8N1, DEBUG_UART_RX_PIN, DEBUG_UART_TX_PIN);
  delay(1000);
  logLine("");
  logLine("[wifi_ap] Test sketch starting...");

  WiFi.mode(WIFI_AP);
  bool apStarted = WiFi.softAP(AP_SSID, AP_PASSWORD);

  logLine(String("[wifi_ap] softAP() -> ") + (apStarted ? "OK" : "FAILED"));
  logLine(String("[wifi_ap] SSID=") + AP_SSID + " IP=" + WiFi.softAPIP().toString());
  logLine("[wifi_ap] Connect your phone to this WiFi network and confirm the IP matches.");
}

void loop() {
  if (millis() - lastStatusPrintMs >= STATUS_PRINT_INTERVAL_MS) {
    lastStatusPrintMs = millis();
    logLine(String("[wifi_ap] clients connected=") + WiFi.softAPgetStationNum());
  }
}
