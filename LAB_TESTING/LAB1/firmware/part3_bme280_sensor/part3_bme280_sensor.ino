/*
 * LAB1, Part 3 - BME280 (pressure + temperature + humidity) digitization
 * over I2C (ESP32).
 *
 * The lab guide's original sensor stage asked for an inertial measurement
 * unit (IMU, accelerometer + gyroscope). The sensor actually available for
 * this build is a Bosch BME280 instead, which measures pressure,
 * temperature, and relative humidity - not motion. There is no
 * accelerometer/gyroscope data in this sketch; "still vs. moving" from the
 * original guide is replaced with "baseline vs. perturbed ambient
 * conditions" (see report/secciones/resultados.tex and discusion.tex).
 *
 * Hardware-imposed rate limit (documented honestly, same spirit as the
 * ESP32 DAC's 8-bit limitation in part2_dac_reconstruction.ino): a BME280
 * forced-mode measurement of all three channels at x1 oversampling takes
 * up to ~9.3 ms per the datasheet (1.25 + 2.3*osrs_t + (2.3*osrs_p+0.575) +
 * (2.3*osrs_h+0.575) ms), i.e. at most ~107 Hz - it physically cannot
 * sustain the 200 Hz used for the IMU/encoder sensor stage. This sketch
 * samples at 100 Hz instead (10 ms period), the closest round number that
 * comfortably fits inside one measurement cycle.
 *
 * - Hardware timer interrupt every 10 ms (100 samples/s) only sets a flag;
 *   the actual I2C transactions (triggering the forced-mode measurement,
 *   polling the status register, reading the data registers - all too slow
 *   for an ISR) and the Serial send both happen in loop().
 *
 * Wiring: BME280 SDA -> GPIO21, SCL -> GPIO22 (ESP32 Wire.begin()
 * defaults), VCC -> 3V3, GND -> GND. I2C address 0x76 (SDO tied low, the
 * common default on most breakout boards) - change BME280_ADDR to 0x77 if
 * the board's SDO pin is tied high instead.
 *
 * Compensation: temperature, pressure, and humidity are compensated
 * on-device from the sensor's factory calibration registers, using Bosch's
 * official floating-point compensation formulas (BME280 datasheet,
 * section 4.2.3) - so the frame already carries physical units, unlike the
 * raw ADC codes sent by part1/part2.
 *
 * Frame format (13 bytes, little-endian):
 *   [0]      0xB6                 sync byte
 *   [1..4]   float temperature_c
 *   [5..8]   float pressure_hpa
 *   [9..12]  float humidity_pct
 */

#include <Wire.h>

const uint8_t BME280_ADDR = 0x76;
const uint32_t SAMPLE_PERIOD_US = 10000; // 10 ms -> 100 Hz (sensor-limited, see header)

// BME280 registers
const uint8_t REG_CALIB_00 = 0x88; // dig_T1..dig_T3, dig_P1..dig_P9 (26 bytes)
const uint8_t REG_CALIB_H1 = 0xA1; // dig_H1 (1 byte)
const uint8_t REG_CALIB_H2 = 0xE1; // dig_H2..dig_H6 (7 bytes)
const uint8_t REG_CTRL_HUM = 0xF2;
const uint8_t REG_CTRL_MEAS = 0xF4;
const uint8_t REG_STATUS = 0xF3;
const uint8_t REG_DATA = 0xF7; // press_msb..hum_lsb (8 bytes)

hw_timer_t *sampleTimer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;
volatile bool sampleReady = false;

// Factory calibration coefficients (read once in setup())
uint16_t dig_T1;
int16_t dig_T2, dig_T3;
uint16_t dig_P1;
int16_t dig_P2, dig_P3, dig_P4, dig_P5, dig_P6, dig_P7, dig_P8, dig_P9;
uint8_t dig_H1, dig_H3;
int16_t dig_H2, dig_H4, dig_H5;
int8_t dig_H6;

double t_fine; // shared intermediate between temperature and pressure/humidity compensation

void bmeWrite(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

void bmeReadBytes(uint8_t reg, uint8_t *buf, uint8_t len) {
  Wire.beginTransmission(BME280_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom((int)BME280_ADDR, (int)len, true);
  for (uint8_t i = 0; i < len; i++) {
    buf[i] = Wire.read();
  }
}

void readCalibration() {
  uint8_t buf[26];
  bmeReadBytes(REG_CALIB_00, buf, 26);
  dig_T1 = (uint16_t)(buf[1] << 8 | buf[0]);
  dig_T2 = (int16_t)(buf[3] << 8 | buf[2]);
  dig_T3 = (int16_t)(buf[5] << 8 | buf[4]);
  dig_P1 = (uint16_t)(buf[7] << 8 | buf[6]);
  dig_P2 = (int16_t)(buf[9] << 8 | buf[8]);
  dig_P3 = (int16_t)(buf[11] << 8 | buf[10]);
  dig_P4 = (int16_t)(buf[13] << 8 | buf[12]);
  dig_P5 = (int16_t)(buf[15] << 8 | buf[14]);
  dig_P6 = (int16_t)(buf[17] << 8 | buf[16]);
  dig_P7 = (int16_t)(buf[19] << 8 | buf[18]);
  dig_P8 = (int16_t)(buf[21] << 8 | buf[20]);
  dig_P9 = (int16_t)(buf[23] << 8 | buf[22]);

  uint8_t h1;
  bmeReadBytes(REG_CALIB_H1, &h1, 1);
  dig_H1 = h1;

  uint8_t hbuf[7];
  bmeReadBytes(REG_CALIB_H2, hbuf, 7);
  dig_H2 = (int16_t)(hbuf[1] << 8 | hbuf[0]);
  dig_H3 = hbuf[2];
  dig_H4 = (int16_t)((hbuf[3] << 4) | (hbuf[4] & 0x0F));
  dig_H5 = (int16_t)((hbuf[5] << 4) | (hbuf[4] >> 4));
  dig_H6 = (int8_t)hbuf[6];
}

// Bosch BME280 datasheet, section 4.2.3, floating-point compensation formulas.
double compensateTemperature(int32_t adc_T) {
  double var1, var2;
  var1 = (((double)adc_T) / 16384.0 - ((double)dig_T1) / 1024.0) * ((double)dig_T2);
  var2 = ((((double)adc_T) / 131072.0 - ((double)dig_T1) / 8192.0) *
          (((double)adc_T) / 131072.0 - ((double)dig_T1) / 8192.0)) * ((double)dig_T3);
  t_fine = var1 + var2;
  return (var1 + var2) / 5120.0; // degrees C
}

double compensatePressure(int32_t adc_P) {
  double var1, var2, p;
  var1 = ((double)t_fine / 2.0) - 64000.0;
  var2 = var1 * var1 * ((double)dig_P6) / 32768.0;
  var2 = var2 + var1 * ((double)dig_P5) * 2.0;
  var2 = (var2 / 4.0) + (((double)dig_P4) * 65536.0);
  var1 = (((double)dig_P3) * var1 * var1 / 524288.0 + ((double)dig_P2) * var1) / 524288.0;
  var1 = (1.0 + var1 / 32768.0) * ((double)dig_P1);
  if (var1 == 0.0) return 0.0; // avoid division by zero (datasheet-recommended guard)
  p = 1048576.0 - (double)adc_P;
  p = (p - (var2 / 4096.0)) * 6250.0 / var1;
  var1 = ((double)dig_P9) * p * p / 2147483648.0;
  var2 = p * ((double)dig_P8) / 32768.0;
  p = p + (var1 + var2 + ((double)dig_P7)) / 16.0;
  return p / 100.0; // Pa -> hPa
}

double compensateHumidity(int32_t adc_H) {
  double var_H = (((double)t_fine) - 76800.0);
  var_H = (adc_H - (((double)dig_H4) * 64.0 + ((double)dig_H5) / 16384.0 * var_H)) *
          (((double)dig_H2) / 65536.0 * (1.0 + ((double)dig_H6) / 67108864.0 * var_H *
          (1.0 + ((double)dig_H3) / 67108864.0 * var_H)));
  var_H = var_H * (1.0 - ((double)dig_H1) * var_H / 524288.0);
  if (var_H > 100.0) var_H = 100.0;
  else if (var_H < 0.0) var_H = 0.0;
  return var_H; // %RH
}

// Triggers one forced-mode measurement, blocks (bounded, ~9.3 ms max) until
// ready, and returns compensated temperature/pressure/humidity. Too slow
// for an ISR - called from loop() only.
void readBme280(float out[3]) {
  bmeWrite(REG_CTRL_HUM, 0x01);  // humidity oversampling x1
  bmeWrite(REG_CTRL_MEAS, 0x25); // temp x1, pressure x1, forced mode (0b001_001_01)

  uint8_t status;
  do {
    bmeReadBytes(REG_STATUS, &status, 1);
  } while (status & 0x08); // bit 3 = "measuring"

  uint8_t data[8];
  bmeReadBytes(REG_DATA, data, 8);

  int32_t adc_P = ((int32_t)data[0] << 12) | ((int32_t)data[1] << 4) | (data[2] >> 4);
  int32_t adc_T = ((int32_t)data[3] << 12) | ((int32_t)data[4] << 4) | (data[5] >> 4);
  int32_t adc_H = ((int32_t)data[6] << 8) | data[7];

  out[0] = (float)compensateTemperature(adc_T); // must run before pressure/humidity (sets t_fine)
  out[1] = (float)compensatePressure(adc_P);
  out[2] = (float)compensateHumidity(adc_H);
}

void IRAM_ATTR onSampleTick() {
  portENTER_CRITICAL_ISR(&timerMux);
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  Wire.begin(); // SDA=GPIO21, SCL=GPIO22 by default on ESP32
  readCalibration();
  Serial.begin(115200); // 3 floats @ 100 Hz needs ~1300 B/s, comfortable margin

  sampleTimer = timerBegin(1000000);              // 1 MHz -> 1 tick = 1 us (Arduino-ESP32 core 3.x timer API)
  timerAttachInterrupt(sampleTimer, &onSampleTick);
  timerAlarm(sampleTimer, SAMPLE_PERIOD_US, true, 0); // period in us, auto-reload, infinite reloads
}

void loop() {
  if (sampleReady) {
    portENTER_CRITICAL(&timerMux);
    sampleReady = false;
    portEXIT_CRITICAL(&timerMux);

    float values[3]; // temperature_c, pressure_hpa, humidity_pct
    readBme280(values); // I2C transactions, done here in loop() not in the ISR

    uint8_t frame[13];
    frame[0] = 0xB6;
    memcpy(&frame[1], values, 12);
    Serial.write(frame, sizeof(frame));
  }
}
