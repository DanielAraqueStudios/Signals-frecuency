/*
 * LAB1, Part 3 - IMU (accelerometer + gyroscope) digitization over I2C
 * (ESP32).
 *
 * Written for an MPU-6050-family IMU (accelerometer + gyroscope, 6
 * channels, I2C) as a common lab-kit choice; swap the register map in
 * readImuRaw() if a different IMU model is actually used, and update the
 * conversion constants (ACCEL_LSB_PER_G / GYRO_LSB_PER_DPS) in
 * pc_logger/serial_logger.py from that model's datasheet - the ones there
 * match the MPU-6050 at its default full-scale ranges (+-2 g, +-250 deg/s).
 *
 * - Hardware timer interrupt every 5 ms (200 samples/s) only sets a flag;
 *   the actual I2C transaction (too slow for an ISR) and Serial send both
 *   happen in loop().
 *
 * Wiring: IMU SDA -> GPIO21, SCL -> GPIO22 (ESP32 Wire.begin() defaults),
 * IMU VCC/GND -> 3V3/GND.
 *
 * Frame format (14 bytes, little-endian) - unchanged from the STM32
 * version:
 *   [0]      0xB5                 sync byte
 *   [1..2]   int16_t ax_raw
 *   [3..4]   int16_t ay_raw
 *   [5..6]   int16_t az_raw
 *   [7..8]   int16_t gx_raw
 *   [9..10]  int16_t gy_raw
 *   [11..12] int16_t gz_raw
 *   [13]     0x00                 reserved/padding
 */

#include <Wire.h>

const uint8_t IMU_ADDR = 0x68;          // MPU-6050 default address (AD0 low)
const uint32_t SAMPLE_PERIOD_US = 5000; // 5 ms -> 200 Hz

hw_timer_t *sampleTimer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;
volatile bool sampleReady = false;

void imuWriteRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

void readImuRaw(int16_t out[6]) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(0x3B); // ACCEL_XOUT_H, MPU-6050 register map
  Wire.endTransmission(false);
  Wire.requestFrom((int)IMU_ADDR, 14, true);

  for (int i = 0; i < 3; i++) {
    out[i] = (Wire.read() << 8) | Wire.read(); // ax, ay, az
  }
  Wire.read(); Wire.read(); // skip TEMP_OUT
  for (int i = 3; i < 6; i++) {
    out[i] = (Wire.read() << 8) | Wire.read(); // gx, gy, gz
  }
}

void IRAM_ATTR onSampleTick() {
  portENTER_CRITICAL_ISR(&timerMux);
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  Wire.begin(); // SDA=GPIO21, SCL=GPIO22 by default on ESP32
  imuWriteRegister(0x6B, 0x00); // MPU-6050: wake from sleep, default clock
  Serial.begin(230400);         // 6 int16 channels @ 200 Hz needs headroom

  sampleTimer = timerBegin(0, 80, true);
  timerAttachInterrupt(sampleTimer, &onSampleTick, true);
  timerAlarmWrite(sampleTimer, SAMPLE_PERIOD_US, true);
  timerAlarmEnable(sampleTimer);
}

void loop() {
  if (sampleReady) {
    portENTER_CRITICAL(&timerMux);
    sampleReady = false;
    portEXIT_CRITICAL(&timerMux);

    int16_t raw[6];
    readImuRaw(raw); // I2C transaction, done here in loop() not in the ISR

    uint8_t frame[14];
    frame[0] = 0xB5;
    memcpy(&frame[1], raw, 12);
    frame[13] = 0x00;
    Serial.write(frame, sizeof(frame));
  }
}
