/*
 * Standalone bring-up sketch: BTS7960 H-bridge (band motor) only.
 *
 * Board: ESP32-WROOM-32. RPWM=GPIO25, LPWM=GPIO26, EN=GPIO27. One
 * direction only -- this rig doesn't need reverse.
 *
 * Open Serial Monitor at 115200 baud.
 *
 * Serial commands:
 *   o        -> toggle motor on/off
 *   +  / -   -> increase / decrease speed (0-255)
 *   s        -> print current state
 */

#define RPWM_PIN 25
#define LPWM_PIN 26
#define EN_PIN   27

int motorSpeed = 200;
bool motorOn = false;

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
  Serial.print("[motor] applyMotor() -> motorOn=");
  Serial.print(motorOn ? "true" : "false");
  Serial.print(" speed=");
  Serial.print(motorSpeed);
  Serial.print(" EN=");
  Serial.print(motorOn ? "HIGH" : "LOW");
  Serial.print(" RPWM=");
  Serial.println(motorOn ? motorSpeed : 0);
}

void printState() {
  Serial.print("[motor] state: motorOn=");
  Serial.print(motorOn ? "ON" : "OFF");
  Serial.print(" speed=");
  Serial.println(motorSpeed);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("[motor] Test sketch starting...");

  pinMode(RPWM_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  applyMotor();  // starts off

  Serial.println("[motor] Pins configured. Commands: o=toggle, +/-=speed, s=state");
}

void loop() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();
  line.toLowerCase();
  if (line.length() == 0) return;

  if (line == "o") {
    motorOn = !motorOn;
    applyMotor();
  } else if (line == "+") {
    motorSpeed = min(255, motorSpeed + 20);
    applyMotor();
  } else if (line == "-") {
    motorSpeed = max(0, motorSpeed - 20);
    applyMotor();
  } else if (line == "s") {
    printState();
  } else {
    Serial.println("[motor] Comando no reconocido. o=toggle, +/-=speed, s=state");
  }
}
