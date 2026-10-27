#include <avr/wdt.h>

#define TEMP_PIN A0
#define HEATER_RL1_PIN 3
#define BUZZER_PIN 4
#define HEATER_RL2_PIN 5

float currentTemp = 74.0;
float targetTemp = 163.0;
bool heaterEnabled = false;
bool boilMode = false;
float lastRawADC = 0;
bool targetReachedAlertSent = false;
bool heatingState = false;

// Heartbeat / Keep-Alive (30s sin señal de Pi = Apagado de seguridad)
unsigned long lastHeartbeat = 0;

void setup() {
  pinMode(HEATER_RL1_PIN, OUTPUT);
  pinMode(HEATER_RL2_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(HEATER_RL1_PIN, LOW);
  digitalWrite(HEATER_RL2_PIN, LOW);
  noTone(BUZZER_PIN);

  Serial.begin(9600);
  pinMode(TEMP_PIN, INPUT);

  wdt_enable(WDTO_2S);
  lastHeartbeat = millis();
}

float leerTemperaturaNTC() {
  long sumRaw = 0;
  int samples = 10;

  for (int i = 0; i < samples; i++) {
    sumRaw += analogRead(TEMP_PIN);
    delay(2);
  }

  float rawADC = (float)sumRaw / samples;
  lastRawADC = rawADC;

  if (rawADC >= 1022.0 || rawADC <= 1.0) return -999.0;

  float tempF = 0.0;

  // Curva de 2 tramos (Piecewise Linear Calibration)
  if (rawADC >= 828.0) {
    // Tramo Alto: Macerado (157.0°F) a Hervor (212.0°F)
    tempF = 157.0 + ((rawADC - 828.0) * 0.8871);
  } else {
    // Tramo Bajo: Temperatura ambiente/tibia hasta Macerado (RAW 777 = 95.9°F a RAW 828 = 157.0°F)
    tempF = 157.0 + ((rawADC - 828.0) * 1.198);
  }

  return tempF;
}

// 1. Triple pitido mediano al llegar a la temperatura objetivo
void playTripleBeep() {
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 2200, 200);
    delay(350);
    wdt_reset();
  }
  noTone(BUZZER_PIN);
}

// 2. Melodía completa al finalizar el Step del perfil automático
void playBuzzerFinish() {
  tone(BUZZER_PIN, 2000, 120); delay(150); wdt_reset();
  tone(BUZZER_PIN, 2000, 120); delay(150); wdt_reset();
  tone(BUZZER_PIN, 2400, 200); delay(220); wdt_reset();
  tone(BUZZER_PIN, 2000, 120); delay(150); wdt_reset();
  tone(BUZZER_PIN, 2000, 120); delay(250); wdt_reset();
  tone(BUZZER_PIN, 2000, 120); delay(150); wdt_reset();
  tone(BUZZER_PIN, 2000, 120); delay(300); wdt_reset();
  tone(BUZZER_PIN, 1500, 250); delay(280); wdt_reset();
  tone(BUZZER_PIN, 1100, 400); delay(400); wdt_reset();
  noTone(BUZZER_PIN);
}

void loop() {
  wdt_reset();

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    lastHeartbeat = millis();

    if (input.startsWith("SET:")) {
      targetTemp = input.substring(4).toFloat();
      targetReachedAlertSent = false;
      if (currentTemp < targetTemp) heatingState = true;
    }
    else if (input == "H:1") {
      heaterEnabled = true;
      boilMode = false;
      targetReachedAlertSent = false;
      if (currentTemp < targetTemp) heatingState = true;
    }
    else if (input == "H:0") {
      heaterEnabled = false;
      boilMode = false;
      targetReachedAlertSent = false;
      heatingState = false;
    }
    else if (input == "H:H") {
      heaterEnabled = true;
      boilMode = true;
      targetReachedAlertSent = false;
    }
    else if (input == "BEEP") { tone(BUZZER_PIN, 2500, 250); }
    else if (input == "BUZZ:ON") { tone(BUZZER_PIN, 2500); }
    else if (input == "BUZZ:OFF") { noTone(BUZZER_PIN); }
    else if (input == "CHINGATU") { playBuzzerFinish(); }
    else if (input == "PING") { }
  }

  // Cortafuegos Heartbeat (30s)
  if ((heaterEnabled || boilMode) && (millis() - lastHeartbeat > 30000)) {
    heaterEnabled = false;
    boilMode = false;
    heatingState = false;
    digitalWrite(HEATER_RL1_PIN, LOW);
    digitalWrite(HEATER_RL2_PIN, LOW);
  }

  float tempF = leerTemperaturaNTC();
  if (tempF > 30.0 && tempF < 250.0) currentTemp = tempF;

  bool state = false;
  if (boilMode) {
    state = true;
    if (currentTemp >= 212.0 && !targetReachedAlertSent) {
      playTripleBeep();
      targetReachedAlertSent = true;
    }
  } else if (heaterEnabled) {
    if (heatingState) {
      if (currentTemp >= targetTemp) {
        heatingState = false;
        state = false;
        digitalWrite(HEATER_RL1_PIN, LOW);
        digitalWrite(HEATER_RL2_PIN, LOW);
        if (!targetReachedAlertSent) {
          playTripleBeep();
          targetReachedAlertSent = true;
        }
      }
    } else {
      if (currentTemp <= (targetTemp - 2.0)) {
        heatingState = true;
      }
    }
    state = heatingState;
  }

  digitalWrite(HEATER_RL1_PIN, state ? HIGH : LOW);
  digitalWrite(HEATER_RL2_PIN, state ? HIGH : LOW);

  static unsigned long lastReport = 0;
  if (millis() - lastReport >= 1000) {
    lastReport = millis();
    String hStatus = boilMode ? "H" : (heaterEnabled ? "1" : "0");

    Serial.print("T:"); Serial.print(currentTemp, 1);
    Serial.print(",SET:"); Serial.print(targetTemp, 1);
    Serial.print(",H:"); Serial.print(hStatus);
    Serial.print(",P:0");
    Serial.print(",RAW:"); Serial.println(lastRawADC, 1);
  }
}
