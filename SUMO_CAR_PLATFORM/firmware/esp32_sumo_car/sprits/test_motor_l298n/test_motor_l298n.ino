/*
 * Standalone bring-up sketch: L298N H-bridge, two DC motors (Sprint 2).
 *
 * Board: ESP32-S3 (e.g. ESP32-S3-DevKitC-1). No WiFi, no HTTP server --
 * this sketch only verifies the motor wiring and direction mapping.
 *
 * Pin mapping (ADJUST to your actual wiring). Chosen in the GPIO 1-21
 * range to stay clear of ESP32-S3 strapping pins (0, 3, 45, 46), the
 * pins reserved for integrated flash/PSRAM (commonly 26-37), and the
 * native USB pins (19/20) on boards that expose USB-OTG:
 *   IN1/IN2 -> left motor direction (L298N input A)
 *   IN3/IN4 -> right motor direction (L298N input B)
 *   ENA     -> left motor speed (PWM, via LEDC under analogWrite)
 *   ENB     -> right motor speed (PWM, via LEDC under analogWrite)
 *
 * On boot, runs one fixed sequence (forward/backward/left/right/stop)
 * with the car propped up so the wheels don't touch the ground. After
 * that, accepts Serial commands for repeated manual testing.
 *
 * Interactive commands still go over the USB-CDC Serial port (unchanged).
 * Diagnostic logs are additionally mirrored to a dedicated hardware UART
 * (DebugUART) so they can be read from an external USB-TTL adapter too.
 *
 * Open Serial Monitor at 115200 baud.
 * Serial commands:
 *   f  -> forward
 *   b  -> backward
 *   l  -> turn left
 *   r  -> turn right
 *   s  -> stop
 *   +/-  -> increase/decrease speed (0-255)
 */

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

// Dedicated hardware UART for debug logging only (separate from the
// USB-CDC Serial used for interactive f/b/l/r/s/+/- commands). Pins
// chosen within the safe GPIO 1-21 range, clear of the L298N pins above
// and of strapping/flash-PSRAM/native-USB pins.
#define DEBUG_UART_TX_PIN 17
#define DEBUG_UART_RX_PIN 18
#define DEBUG_UART_BAUD 115200
HardwareSerial DebugUART(1);

int motorSpeed = 200;

void logLine(const String &msg) {
  Serial.println(msg);
  DebugUART.println(msg);
}

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
  logLine("[motor] motorStop()");
}

void motorForward(int speed) {
  setLeftMotor(true, false, speed);
  setRightMotor(true, false, speed);
  logLine(String("[motor] motorForward() speed=") + speed);
}

void motorBackward(int speed) {
  setLeftMotor(false, true, speed);
  setRightMotor(false, true, speed);
  logLine(String("[motor] motorBackward() speed=") + speed);
}

void motorLeft(int speed) {
  // Spin in place: left wheel backward, right wheel forward.
  setLeftMotor(false, true, speed);
  setRightMotor(true, false, speed);
  logLine(String("[motor] motorLeft() speed=") + speed);
}

void motorRight(int speed) {
  // Spin in place: left wheel forward, right wheel backward.
  setLeftMotor(true, false, speed);
  setRightMotor(false, true, speed);
  logLine(String("[motor] motorRight() speed=") + speed);
}

void printState() {
  logLine(String("[motor] state: speed=") + motorSpeed);
}

void runFixedSequence() {
  logLine("[motor] Running fixed bring-up sequence (car must be propped up)...");
  motorForward(motorSpeed);
  delay(1000);
  motorStop();
  delay(500);
  motorBackward(motorSpeed);
  delay(1000);
  motorStop();
  delay(500);
  motorLeft(motorSpeed);
  delay(1000);
  motorStop();
  delay(500);
  motorRight(motorSpeed);
  delay(1000);
  motorStop();
  logLine("[motor] Fixed sequence done.");
}

void setup() {
  Serial.begin(115200);
  DebugUART.begin(DEBUG_UART_BAUD, SERIAL_8N1, DEBUG_UART_RX_PIN, DEBUG_UART_TX_PIN);
  delay(1000);
  logLine("");
  logLine("[motor] Test sketch starting...");

  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  pinMode(IN3_PIN, OUTPUT);
  pinMode(IN4_PIN, OUTPUT);
  pinMode(ENA_PIN, OUTPUT);
  pinMode(ENB_PIN, OUTPUT);
  motorStop();

  runFixedSequence();

  logLine("[motor] Commands: f/b/l/r/s, +/- speed");
}

void loop() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();
  line.toLowerCase();
  if (line.length() == 0) return;

  if (line == "f") {
    motorForward(motorSpeed);
  } else if (line == "b") {
    motorBackward(motorSpeed);
  } else if (line == "l") {
    motorLeft(motorSpeed);
  } else if (line == "r") {
    motorRight(motorSpeed);
  } else if (line == "s") {
    motorStop();
  } else if (line == "+") {
    motorSpeed = min(255, motorSpeed + 20);
    printState();
  } else if (line == "-") {
    motorSpeed = max(0, motorSpeed - 20);
    printState();
  } else {
    logLine("[motor] Comando no reconocido. f/b/l/r/s, +/- speed");
  }
}
