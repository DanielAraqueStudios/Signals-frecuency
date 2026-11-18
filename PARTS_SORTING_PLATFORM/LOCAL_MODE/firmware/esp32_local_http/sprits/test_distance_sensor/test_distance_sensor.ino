/*
 * Standalone bring-up sketch: VL53L0X time-of-flight distance sensor,
 * used to stop the band when a part is under the camera and resume once
 * it has passed.
 *
 * Board: ESP32-WROOM-32. Pinout matches the GLOBAL sketch
 * (../../esp32_local_http.ino) exactly, so this test doesn't collide with
 * any other module's pins and the wiring carries over unchanged once
 * integrated:
 *   - VL53L0X: I2C, SDA=GPIO21, SCL=GPIO22 (same bus as the LCD, default
 *     VL53L0X address 0x29 vs the LCD's 0x27 -- no conflict).
 *   - Band motor: BTS7960 H-bridge, RPWM=GPIO25, LPWM=GPIO26, EN=GPIO27
 *     (same as test_motor.ino and the main sketch). The pasted reference
 *     logic drove the band with a single digitalWrite on GPIO4 -- that
 *     pin isn't used anywhere else in this project, but driving the band
 *     through the H-bridge (not a bare GPIO) keeps every sketch
 *     consistent with the real hardware, so this logic is reused as-is
 *     when merged into the main sketch.
 *
 * Open Serial Monitor at 115200 baud.
 */

#include <Wire.h>
#include "Adafruit_VL53L0X.h"

Adafruit_VL53L0X lox = Adafruit_VL53L0X();

// ---------------------------------------------------------------------
// Band motor (BTS7960 H-bridge) -- same pins/logic as test_motor.ino and
// the main sketch's motor control, one direction only.
// ---------------------------------------------------------------------
#define RPWM_PIN 25
#define LPWM_PIN 26
#define EN_PIN   27
int motorSpeed = 200;  // 0-255
bool motorOn = true;   // band runs by default; stops when an object is detected

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
// Distance thresholds (mm). An object under the camera reads below
// DISTANCIA_UMBRAL, and we wait for the reading to climb back past
// DISTANCIA_LIBRE before resuming.
// ---------------------------------------------------------------------
const int DISTANCIA_UMBRAL = 80;
const int DISTANCIA_LIBRE = 85;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("[distance] Test sketch starting...");

  pinMode(RPWM_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  applyMotor();  // band starts moving

  Wire.begin(21, 22);
  Serial.println("[distance] Calling lox.begin()...");
  if (!lox.begin()) {
    Serial.println("[distance] ERROR: no se pudo iniciar el sensor VL53L0X. Revisa SDA=21/SCL=22 y 3V3.");
    while (true) {
      delay(1000);
    }
  }
  Serial.println("[distance] Sensor listo. Banda en movimiento.");
}

void loop() {
  VL53L0X_RangingMeasurementData_t measure;
  lox.rangingTest(&measure, false);

  if (measure.RangeStatus != 4) {
    int distancia = measure.RangeMilliMeter;

    Serial.print("[distance] Distancia actual: ");
    Serial.print(distancia);
    Serial.println(" mm");

    if (distancia < DISTANCIA_UMBRAL && distancia > 0) {
      Serial.println("[distance] Objeto detectado! Deteniendo banda...");
      motorOn = false;
      applyMotor();

      Serial.println("[distance] Tomando foto...");
      delay(5000);

      Serial.println("[distance] Foto terminada. Reanudando banda...");
      motorOn = true;
      applyMotor();

      Serial.println("[distance] Esperando a que el objeto abandone el sensor...");
      bool objetoPaso = false;
      while (!objetoPaso) {
        lox.rangingTest(&measure, false);
        if (measure.RangeStatus != 4 && measure.RangeMilliMeter > DISTANCIA_LIBRE) {
          objetoPaso = true;
        }
        delay(50);
      }

      Serial.println("[distance] El objeto ya paso. Listo para el siguiente.");
      Serial.println("-----------------------------------");
    }
  } else {
    Serial.println("[distance] WARN: RangeStatus=4 (lectura fuera de rango), ignorando muestra.");
  }

  delay(100);
}
