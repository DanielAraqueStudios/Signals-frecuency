/*
 * Item 4(c) - Arduino Uno, hardware-timer interrupt sampling.
 *
 * Same mechanism as esp32_c_interrupt, ported to the Uno's ATmega328P
 * using Timer1 in CTC mode instead of the ESP32's timerBegin API. Timer1
 * (16-bit) is clocked from the 16 MHz system clock through a /1024
 * prescaler, giving a 15625 Hz tick rate; OCR1A = 1562 yields an interrupt
 * period of (1562 + 1) / 15625 s = 100.032 ms - the closest integer-OCR1A
 * approximation to the requested 100 ms with this prescaler.
 *
 * The ISR only sets a flag with a timestamp (ISRs must stay short: no
 * Serial/analogRead inside the ISR itself). loop() checks the flag,
 * performs the actual potentiometer reads and the Serial print, then goes
 * back to the same blocking summation workload as 4(a). Since Timer1 is a
 * hardware peripheral independent of the main code path, the *timestamp*
 * of each sample request stays accurate even while loop() is busy
 * summing; only the *processing* of that request is delayed until loop()
 * next checks the flag.
 *
 * The Uno has no second core, so there is no dual-core (4b) variant for
 * this board - only 4(a) and 4(c) apply, per the assignment.
 *
 * Wiring: potentiometer wipers -> A0, A1, A2. Outer legs -> 5V and GND
 * (the Uno's ADC reference is 5V, unlike the ESP32's 3.3V).
 */

const int POT_PINS[3] = {A0, A1, A2};

// Swap this between runs: 1000000UL, 10000000UL, 100000000UL
const unsigned long SUM_LIMIT = 10000000UL;

volatile bool sampleReady = false;
volatile unsigned long lastIsrMs = 0;
volatile unsigned long isrDeltaMs = 0;

ISR(TIMER1_COMPA_vect) {
  unsigned long now = millis();
  isrDeltaMs = now - lastIsrMs;
  lastIsrMs = now;
  sampleReady = true;
}

void setup() {
  Serial.begin(115200);
  lastIsrMs = millis();

  noInterrupts();
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1 = 0;
  OCR1A = 1562;                          // ~100.032 ms period, see header comment
  TCCR1B |= (1 << WGM12);                // CTC mode
  TCCR1B |= (1 << CS12) | (1 << CS10);   // prescaler = 1024
  TIMSK1 |= (1 << OCIE1A);               // enable Timer1 compare-A interrupt
  interrupts();
}

void loop() {
  if (sampleReady) {
    noInterrupts();
    unsigned long dt = isrDeltaMs;
    sampleReady = false;
    interrupts();

    int a = analogRead(POT_PINS[0]); // 10-bit: 0-1023
    int b = analogRead(POT_PINS[1]);
    int c = analogRead(POT_PINS[2]);

    Serial.print(F("[isr] dt_ms="));
    Serial.print(dt);
    Serial.print(F(" pot1="));
    Serial.print(a);
    Serial.print(F(" pot2="));
    Serial.print(b);
    Serial.print(F(" pot3="));
    Serial.println(c);
  }

  // Same blocking summation workload as 4(a), left in loop() on purpose:
  // the interrupt still fires on time underneath it.
  volatile unsigned long long sum = 0;
  for (unsigned long i = 0; i < SUM_LIMIT; i++) {
    sum += i;
  }
}
