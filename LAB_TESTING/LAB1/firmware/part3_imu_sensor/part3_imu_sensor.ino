/*
 * LAB1, Part 3 - IMU (accelerometer + gyroscope) digitization over I2C.
 *
 * Written for an MPU-6050-family IMU (accelerometer + gyroscope, 6
 * channels, I2C) as a common lab-kit choice; swap the register map in
 * readImuRaw() if a different IMU model is actually used, and update the
 * conversion constants (ACCEL_SCALE / GYRO_SCALE) from that model's
 * datasheet - the ones below match the MPU-6050 at its default full-scale
 * ranges (+-2 g, +-250 deg/s).
 *
 * - HardwareTimer interrupt every 5 ms (200 samples/s).
 * - Each interrupt reads all 6 channels (ax, ay, az, gx, gy, gz) over I2C
 *   and sends them to the PC as one binary frame; conversion to physical
 *   units (m/s^2, rad/s) is done PC-side by pc_logger/serial_logger.py so
 *   the ISR stays short.
 *
 * Wiring: IMU SDA/SCL -> the board's I2C1 pins (PB7/PB6 on most Nucleo-64
 * boards), IMU VCC/GND -> 3V3/GND.
 *
 * Frame format (14 bytes, little-endian):
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
#include <HardwareTimer.h>

const uint8_t IMU_ADDR = 0x68;         // MPU-6050 default address (AD0 low)
const uint32_t SAMPLE_PERIOD_US = 5000; // 5 ms -> 200 Hz

HardwareTimer sampleTimer(TIM2);
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
  Wire.requestFrom(IMU_ADDR, (uint8_t)14, (uint8_t) true);

  for (int i = 0; i < 3; i++) {
    out[i] = (Wire.read() << 8) | Wire.read(); // ax, ay, az
  }
  Wire.read(); Wire.read(); // skip TEMP_OUT
  for (int i = 3; i < 6; i++) {
    out[i] = (Wire.read() << 8) | Wire.read(); // gx, gy, gz
  }
}

void onSampleTick() {
  sampleReady = true;
}

void setup() {
  Wire.begin();
  imuWriteRegister(0x6B, 0x00); // MPU-6050: wake from sleep, default clock
  Serial.begin(230400);         // 6 int16 channels @ 200 Hz needs headroom

  sampleTimer.setOverflow(SAMPLE_PERIOD_US, MICROSEC_FORMAT);
  sampleTimer.attachInterrupt(onSampleTick);
  sampleTimer.resume();
}

void loop() {
  if (sampleReady) {
    sampleReady = false;

    int16_t raw[6];
    readImuRaw(raw); // I2C transaction is too slow for the ISR itself; done here in loop()

    uint8_t frame[14];
    frame[0] = 0xB5;
    memcpy(&frame[1], raw, 12);
    frame[13] = 0x00;
    Serial.write(frame, sizeof(frame));
  }
}
