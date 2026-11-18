/*
 * Standalone bring-up sketch: fingerprint sensor only.
 *
 * Board: ESP32-WROOM-32. Sensor on HardwareSerial(2), RX=GPIO16,
 * TX=GPIO17, 57600 baud, powered at 3V3 (NOT 5V).
 *
 * Open Serial Monitor at 115200 baud. Logs every step so sensor wiring
 * problems are visible immediately instead of guessed at.
 *
 * Serial commands:
 *   l        -> list occupied fingerprint IDs
 *   n        -> enroll at next free ID
 *   r <id>   -> enroll at a specific ID (e.g. r 5)
 *   b <id>   -> delete a specific ID
 *   vaciar   -> erase ALL stored fingerprints (asks to confirm with 'si')
 *   (no command) -> continuously scans and logs finger reads
 */

#include <Adafruit_Fingerprint.h>

HardwareSerial fingerSerial(2);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&fingerSerial);

bool awaitingEraseAllConfirm = false;

void printMenu() {
  Serial.println();
  Serial.println("========== FINGERPRINT TEST MENU ==========");
  Serial.println(" l        -> listar IDs ocupados");
  Serial.println(" n        -> registrar en siguiente ID libre");
  Serial.println(" r <id>   -> registrar en ese ID (ej: r 5)");
  Serial.println(" b <id>   -> borrar ese ID (ej: b 5)");
  Serial.println(" vaciar   -> borrar TODAS las huellas");
  Serial.println("============================================");
}

void listFingerprints() {
  finger.getTemplateCount();
  Serial.print("[fingerprint] Huellas guardadas: ");
  Serial.println(finger.templateCount);
  Serial.print("[fingerprint] IDs ocupados: ");
  bool any = false;
  for (int id = 1; id <= 127; id++) {
    if (finger.loadModel(id) == FINGERPRINT_OK) {
      Serial.print(id);
      Serial.print(" ");
      any = true;
    }
  }
  if (!any) Serial.print("(ninguno)");
  Serial.println();
}

int firstFreeId() {
  for (int id = 1; id <= 127; id++) {
    if (finger.loadModel(id) != FINGERPRINT_OK) return id;
  }
  return -1;
}

uint8_t waitForImage(unsigned long ms) {
  unsigned long t = millis();
  uint8_t p = FINGERPRINT_NOFINGER;
  while (millis() - t < ms) {
    p = finger.getImage();
    if (p == FINGERPRINT_OK) return p;
    delay(30);
  }
  Serial.print("[fingerprint] waitForImage timeout, last status=");
  Serial.println(p);
  return p;
}

bool enrollFingerprint(uint8_t id) {
  Serial.print("[fingerprint] Coloca el dedo para registrar el ID #");
  Serial.println(id);

  uint8_t p = waitForImage(15000);
  if (p != FINGERPRINT_OK) {
    Serial.println("[fingerprint] Tiempo agotado esperando el primer dedo.");
    return false;
  }
  Serial.println("[fingerprint] Imagen 1 capturada, procesando...");
  if (finger.image2Tz(1) != FINGERPRINT_OK) {
    Serial.println("[fingerprint] ERROR al procesar la primera imagen.");
    return false;
  }

  Serial.println("[fingerprint] Retira el dedo...");
  delay(1500);
  unsigned long t = millis();
  while (finger.getImage() != FINGERPRINT_NOFINGER) {
    delay(50);
    if (millis() - t > 10000) break;
  }

  Serial.println("[fingerprint] Coloca el MISMO dedo otra vez...");
  p = waitForImage(15000);
  if (p != FINGERPRINT_OK) {
    Serial.println("[fingerprint] Tiempo agotado esperando el segundo dedo.");
    return false;
  }
  Serial.println("[fingerprint] Imagen 2 capturada, procesando...");
  if (finger.image2Tz(2) != FINGERPRINT_OK) {
    Serial.println("[fingerprint] ERROR al procesar la segunda imagen.");
    return false;
  }
  if (finger.createModel() != FINGERPRINT_OK) {
    Serial.println("[fingerprint] ERROR: las dos lecturas no coinciden.");
    return false;
  }
  if (finger.storeModel(id) == FINGERPRINT_OK) {
    Serial.print("[fingerprint] OK: huella guardada en ID ");
    Serial.println(id);
    return true;
  }
  Serial.println("[fingerprint] ERROR al guardar en el sensor.");
  return false;
}

void handleSerialMenu() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();
  line.toLowerCase();
  if (line.length() == 0) return;

  if (awaitingEraseAllConfirm) {
    awaitingEraseAllConfirm = false;
    if (line == "si") {
      bool ok = finger.emptyDatabase() == FINGERPRINT_OK;
      Serial.println(ok ? "[fingerprint] Todas las huellas borradas." : "[fingerprint] ERROR al vaciar.");
    } else {
      Serial.println("[fingerprint] Cancelado.");
    }
    return;
  }

  if (line == "l") {
    listFingerprints();
  } else if (line == "n") {
    int id = firstFreeId();
    if (id == -1) Serial.println("[fingerprint] No hay IDs libres.");
    else enrollFingerprint(id);
  } else if (line == "vaciar") {
    Serial.println("[fingerprint] Seguro? Escribe 'si' para borrar TODAS las huellas.");
    awaitingEraseAllConfirm = true;
  } else if (line.startsWith("r ")) {
    int id = line.substring(2).toInt();
    if (id >= 1 && id <= 127) enrollFingerprint(id);
    else Serial.println("[fingerprint] ID invalido (1 a 127).");
  } else if (line.startsWith("b ")) {
    int id = line.substring(2).toInt();
    if (id >= 1 && id <= 127) {
      bool ok = finger.deleteModel(id) == FINGERPRINT_OK;
      Serial.println(ok ? "[fingerprint] Borrada." : "[fingerprint] ERROR al borrar.");
    } else {
      Serial.println("[fingerprint] ID invalido (1 a 127).");
    }
  } else {
    printMenu();
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("[fingerprint] Test sketch starting...");

  fingerSerial.begin(57600, SERIAL_8N1, 16, 17);
  delay(500);

  Serial.println("[fingerprint] Calling finger.verifyPassword()...");
  if (finger.verifyPassword()) {
    Serial.println("[fingerprint] OK: sensor detectado.");
  } else {
    Serial.println("[fingerprint] ERROR: sensor NO detectado. Revisa cableado (RX16/TX17) y 3V3.");
    Serial.println("[fingerprint] Sketch continua de todas formas para permitir reintentos.");
  }

  listFingerprints();
  printMenu();
}

void loop() {
  handleSerialMenu();

  int r = finger.getImage();
  if (r == FINGERPRINT_OK) {
    Serial.println("[fingerprint] Imagen capturada, buscando coincidencia...");
    if (finger.image2Tz() != FINGERPRINT_OK) {
      Serial.println("[fingerprint] WARN: image2Tz fallo.");
    } else if (finger.fingerFastSearch() == FINGERPRINT_OK) {
      Serial.print("[fingerprint] MATCH: ID=");
      Serial.print(finger.fingerID);
      Serial.print(" confidence=");
      Serial.println(finger.confidence);
    } else {
      Serial.println("[fingerprint] NO match (huella no reconocida).");
    }
    delay(1000);  // avoid re-triggering while the finger is still down
  }

  delay(50);
}
