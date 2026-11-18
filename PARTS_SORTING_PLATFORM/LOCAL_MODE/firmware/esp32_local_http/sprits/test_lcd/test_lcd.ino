/*
 * Standalone bring-up sketch: 16x2 I2C LCD only.
 *
 * Board: ESP32-WROOM-32. LCD (PCF8574 backpack), SDA=GPIO21, SCL=GPIO22.
 * Default I2C address assumed 0x27 -- if lcd.init() produces a blank
 * screen, this sketch first scans the I2C bus and logs every address
 * found, since 0x3F is the other common backpack address.
 *
 * Open Serial Monitor at 115200 baud.
 */

#include <LiquidCrystal_I2C.h>
#include <Wire.h>

#define LCD_ADDR 0x27
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);

void scanI2CBus() {
  Serial.println("[lcd] Scanning I2C bus...");
  uint8_t found = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();
    if (err == 0) {
      Serial.print("[lcd] Device found at 0x");
      Serial.println(addr, HEX);
      found++;
    }
  }
  if (found == 0) {
    Serial.println("[lcd] No I2C devices found. Check SDA=21/SCL=22 wiring and power.");
  } else {
    Serial.print("[lcd] Total devices found: ");
    Serial.println(found);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("[lcd] Test sketch starting...");

  Wire.begin(21, 22);
  scanI2CBus();

  Serial.print("[lcd] Calling lcd.init() at address 0x");
  Serial.println(LCD_ADDR, HEX);
  lcd.init();
  lcd.backlight();
  Serial.println("[lcd] init() + backlight() done.");

  lcd.setCursor(0, 0);
  lcd.print("LCD test OK");
  lcd.setCursor(0, 1);
  lcd.print("line2 works");
  Serial.println("[lcd] Printed static test text. If the screen is blank, check contrast pot / 0x3F address.");
}

void loop() {
  static unsigned long lastToggle = 0;
  static uint32_t counter = 0;

  if (millis() - lastToggle >= 1000) {
    lastToggle = millis();
    counter++;

    lcd.setCursor(0, 0);
    lcd.print("Tick: ");
    lcd.print(counter);
    lcd.print("   ");  // pad to clear leftover digits

    Serial.print("[lcd] tick=");
    Serial.println(counter);
  }
}
