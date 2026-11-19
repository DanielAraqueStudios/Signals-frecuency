/*
 * Diagnostic-only sketch: continuous heartbeat over both serial ports.
 *
 * Board: ESP32-S3 (e.g. ESP32-S3-DevKitC-1).
 *
 * Purpose: verify that the serial link (USB-CDC and/or the external
 * DebugUART on TX=17/RX=18) is actually alive and readable from outside
 * Arduino IDE, independent of any WiFi/HTTP/motor logic. Prints a counter
 * line once per second, forever, on BOTH:
 *   - Serial    (USB-CDC, native USB port, 115200 baud)
 *   - DebugUART (HardwareSerial(1), 115200 baud, TX=17/RX=18)
 * plus WiFi AP status (SSID, IP, connected clients) so it also doubles as
 * a quick AP sanity check without the full HTTP server.
 *
 * Not part of the sumo-car sprint sequence (0-5) -- this is a standalone
 * tool to debug the serial/port setup itself. Safe to flash at any point;
 * it does not touch the L298N pins.
 *
 * How to use:
 *   1. Flash this sketch.
 *   2. Open Arduino IDE Serial Monitor at 115200 baud, OR connect an
 *      external USB-TTL adapter to TX=17/RX=18 and read it with any
 *      terminal program at 115200 baud, OR read the native USB-CDC COM
 *      port with any serial tool.
 *   3. You should see a new line every ~1000 ms, forever, with an
 *      incrementing counter -- confirms the port is alive and the board
 *      has not frozen/reset silently.
 */

#include <WiFi.h>

#define AP_SSID "SumoCar"
#define AP_PASSWORD "sumo1234"  // WPA2 requires >= 8 chars

#define DEBUG_UART_TX_PIN 17
#define DEBUG_UART_RX_PIN 18
#define DEBUG_UART_BAUD 115200
HardwareSerial DebugUART(1);

#define HEARTBEAT_INTERVAL_MS 1000
unsigned long lastHeartbeatMs = 0;
unsigned long heartbeatCount = 0;

void logLine(const String &msg) {
  Serial.println(msg);
  DebugUART.println(msg);
}

void setup() {
  Serial.begin(115200);
  DebugUART.begin(DEBUG_UART_BAUD, SERIAL_8N1, DEBUG_UART_RX_PIN, DEBUG_UART_TX_PIN);
  delay(1000);
  logLine("");
  logLine("[heartbeat] Diagnostic sketch starting...");
  logLine(String("[heartbeat] Chip model=") + ESP.getChipModel() +
          " revision=" + ESP.getChipRevision() +
          " cores=" + ESP.getChipCores());

  WiFi.mode(WIFI_AP);
  bool apStarted = WiFi.softAP(AP_SSID, AP_PASSWORD);
  logLine(String("[heartbeat] softAP() -> ") + (apStarted ? "OK" : "FAILED"));
  logLine(String("[heartbeat] SSID=") + AP_SSID + " IP=" + WiFi.softAPIP().toString());
  logLine("[heartbeat] Printing one line per second, forever. Reset the board any time to confirm reconnection.");
}

void loop() {
  if (millis() - lastHeartbeatMs >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatMs = millis();
    heartbeatCount++;
    logLine(String("[heartbeat] n=") + heartbeatCount +
            " uptime_ms=" + millis() +
            " free_heap=" + ESP.getFreeHeap() +
            " ap_clients=" + WiFi.softAPgetStationNum() +
            " ap_ip=" + WiFi.softAPIP().toString());
  }
}
