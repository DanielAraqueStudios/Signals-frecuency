/*
 * LAB1, Part 2 - Signal reconstruction via PWM + external low-pass filter.
 *
 * Same 2 ms capture ISR as the other part-2 sketch, but instead of the
 * onboard DAC, the captured code sets the duty cycle of a PWM output.
 * PWM_FREQUENCY_HZ = 5000 Hz satisfies the assignment's ">= 10x the 500 Hz
 * sample rate" and ">= 5 kHz" requirements simultaneously.
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
 *   - ADC_PIN (A0 / PA0)   -> wave generator output.
 *   - PWM_PIN (D9 / PB10, or any STM32 timer-capable PWM pin)
 *     -> input of the external active low-pass filter -> oscilloscope
 *        channel 2 (filter output), compared against the generator on
 *        channel 1.
 *
 * Duty cycle mapping: ADC code 0 -> 1% duty, ADC code 4095 -> 99% duty,
 * linearly interpolated, per the assignment's recommendation.
 */

#include <HardwareTimer.h>

const int ADC_PIN = PA0;
const int PWM_PIN = PB10;
const uint32_t SAMPLE_PERIOD_US = 2000;   // 2 ms -> 500 Hz sampling
const uint32_t PWM_FREQUENCY_HZ = 5000;   // >= 10x sample rate, >= 5 kHz
const int ADC_MAX_CODE = 4095;            // 12-bit

const float DUTY_MIN_PERCENT = 1.0f;
const float DUTY_MAX_PERCENT = 99.0f;

HardwareTimer sampleTimer(TIM2);
HardwareTimer pwmTimer(TIM3);

float codeToDutyPercent(uint16_t code) {
  float frac = (float)code / (float)ADC_MAX_CODE;
  return DUTY_MIN_PERCENT + frac * (DUTY_MAX_PERCENT - DUTY_MIN_PERCENT);
}

void onSampleTick() {
  uint16_t code = analogRead(ADC_PIN);
  pwmTimer.setCaptureCompare(1, codeToDutyPercent(code), PERCENT_COMPARE_FORMAT);

  uint8_t frame[3] = {0xA5, (uint8_t)(code & 0xFF), (uint8_t)(code >> 8)};
  Serial.write(frame, sizeof(frame));
}

void setup() {
  analogReadResolution(12);
  Serial.begin(115200);

  pinMode(PWM_PIN, OUTPUT);
  pwmTimer.setMode(1, TIMER_OUTPUT_COMPARE_PWM1, PWM_PIN);
  pwmTimer.setOverflow(PWM_FREQUENCY_HZ, HERTZ_FORMAT);
  pwmTimer.setCaptureCompare(1, DUTY_MIN_PERCENT, PERCENT_COMPARE_FORMAT);
  pwmTimer.resume();

  sampleTimer.setOverflow(SAMPLE_PERIOD_US, MICROSEC_FORMAT);
  sampleTimer.attachInterrupt(onSampleTick);
  sampleTimer.resume();
}

void loop() {}
