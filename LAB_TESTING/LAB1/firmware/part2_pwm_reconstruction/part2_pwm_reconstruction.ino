/*
 * LAB1, Part 2 - Signal reconstruction via PWM + external low-pass filter
 * (ESP32, using the LEDC peripheral instead of STM32 hardware timers).
 *
 * PWM_FREQUENCY_HZ = 5000 Hz satisfies the assignment's ">= 10x the 500 Hz
 * sample rate" and ">= 5 kHz" requirements simultaneously.
 * PWM_RESOLUTION_BITS = 10 (1024 duty levels) comfortably fits the LEDC
 * peripheral's clock budget at 5 kHz (5000 * 1024 = 5.12 MHz, well under
 * the 80 MHz APB clock LEDC derives from).
 *
 * The PWM pin must be followed externally by an active low-pass filter
 * with ~0 dB gain at the 500 Hz sample rate and <= -20 dB by 600 Hz (100 Hz
 * above it), per the assignment - that filter is analog hardware, not
 * firmware, and is not implemented here; see report/secciones/metodologia.tex
 * for the filter design notes (a 2nd-order Sallen-Key low-pass is
 * suggested, since a single RC stage cannot reach -20 dB within 100 Hz of
 * a 500 Hz cutoff).
 *
 * Wiring:
 *   - ADC_PIN (GPIO34)  -> wave generator output.
 *   - PWM_PIN (GPIO26, any LEDC-capable GPIO)
 *     -> input of the external active low-pass filter -> oscilloscope
 *        channel 2 (filter output), compared against the generator on
 *        channel 1.
 *
 * Duty cycle mapping: ADC code 0 -> 1% duty, ADC code 4095 -> 99% duty,
 * linearly interpolated, per the assignment's recommendation.
 */

const int ADC_PIN = 34;
const int PWM_PIN = 26;
const int PWM_CHANNEL = 0;
const uint32_t SAMPLE_PERIOD_US = 2000;      // 2 ms -> 500 Hz sampling
const uint32_t PWM_FREQUENCY_HZ = 5000;      // >= 10x sample rate, >= 5 kHz
const int PWM_RESOLUTION_BITS = 10;          // 1024 duty levels
const int ADC_MAX_CODE = 4095;               // 12-bit

const float DUTY_MIN_FRAC = 0.01f;
const float DUTY_MAX_FRAC = 0.99f;

hw_timer_t *sampleTimer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

volatile bool sampleReady = false;
volatile uint16_t latestCode = 0;

uint32_t codeToDuty(uint16_t code) {
  float frac = (float)code / (float)ADC_MAX_CODE;
  float duty_frac = DUTY_MIN_FRAC + frac * (DUTY_MAX_FRAC - DUTY_MIN_FRAC);
  return (uint32_t)(duty_frac * ((1 << PWM_RESOLUTION_BITS) - 1));
}

void IRAM_ATTR onSampleTick() {
  portENTER_CRITICAL_ISR(&timerMux);
  uint16_t code = analogRead(ADC_PIN);
  ledcWrite(PWM_CHANNEL, codeToDuty(code));
  latestCode = code;
  sampleReady = true;
  portEXIT_CRITICAL_ISR(&timerMux);
}

void setup() {
  analogReadResolution(12);
  Serial.begin(115200);

  ledcSetup(PWM_CHANNEL, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcAttachPin(PWM_PIN, PWM_CHANNEL);
  ledcWrite(PWM_CHANNEL, codeToDuty(0));

  sampleTimer = timerBegin(0, 80, true);
  timerAttachInterrupt(sampleTimer, &onSampleTick, true);
  timerAlarmWrite(sampleTimer, SAMPLE_PERIOD_US, true);
  timerAlarmEnable(sampleTimer);
}

void loop() {
  if (sampleReady) {
    portENTER_CRITICAL(&timerMux);
    uint16_t code = latestCode;
    sampleReady = false;
    portEXIT_CRITICAL(&timerMux);

    uint8_t frame[3] = {0xA5, (uint8_t)(code & 0xFF), (uint8_t)(code >> 8)};
    Serial.write(frame, sizeof(frame));
  }
}
