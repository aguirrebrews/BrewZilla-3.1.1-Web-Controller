#include <avr/wdt.h>

#define TEMP_PIN A0
#define HEATER_RL1_PIN 3
#define BUZZER_PIN 4
#define HEATER_RL2_PIN 5

enum SystemState {
  STATE_NORMAL,
  STATE_SENSOR_FAULT
};

SystemState currentState = STATE_NORMAL;

float currentTemp = 74.0;
float targetTemp = 163.0;
bool heaterEnabled = false;
bool boilMode = false;
float lastRawADC = 0;

unsigned long lastPingTime = 0;
const unsigned long PING_TIMEOUT = 30000;

float leerTemperaturaNTC() {
  int raw = analogRead(TEMP_PIN);
  lastRawADC = raw;

  if (raw >= 1022 || raw <= 1) {
    return -999.0;
  }

  float resistencia = 10000.0 * (1023.0 / (float)raw - 1.0);
  float logR = log(resistencia);
  float tempK = 1.0 / (0.001129148 + (0.000234125 * logR) + (0.0000000876741 * logR * logR * logR));
  float tempC = tempK - 273.15;
  float tempF = (tempC * 9.0 / 5.0) + 32.0;

  return tempF;
}

void setup() {
  pinMode(HEATER_RL1_PIN, OUTPUT);
  pinMode(HEATER_RL2_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(HEATER_RL1_PIN, LOW);
  digitalWrite(HEATER_RL2_PIN, LOW);
  noTone(BUZZER_PIN);

  Serial.begin(9600);
  pinMode(TEMP_PIN, INPUT);

  lastPingTime = millis();
  wdt_enable(WDTO_2S);
}

void loop() {
  wdt_reset();

  float tempLectura = leerTemperaturaNTC();

  if (tempLectura == -999.0) {
    currentState = STATE_SENSOR_FAULT;
    digitalWrite(HEATER_RL1_PIN, LOW);
    digitalWrite(HEATER_RL2_PIN, LOW);
    heaterEnabled = false;
  } else {
    currentState = STATE_NORMAL;
    currentTemp = tempLectura;
  }

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input == "PING") {
      lastPingTime = millis();
    } else if (input.startsWith("SET_TEMP:")) {
      targetTemp = input.substring(9).toFloat();
    } else if (input == "HEATER_ON") {
      if (currentState != STATE_SENSOR_FAULT) {
        heaterEnabled = true;
      }
    } else if (input == "HEATER_OFF") {
      heaterEnabled = false;
    } else if (input == "BOIL_ON") {
      boilMode = true;
    } else if (input == "BOIL_OFF") {
      boilMode = false;
    }
  }

  if (millis() - lastPingTime > PING_TIMEOUT) {
    digitalWrite(HEATER_RL1_PIN, LOW);
    digitalWrite(HEATER_RL2_PIN, LOW);
    heaterEnabled = false;
  }

  if (currentState == STATE_NORMAL && heaterEnabled) {
    if (currentTemp < targetTemp) {
      digitalWrite(HEATER_RL1_PIN, HIGH);
      if (boilMode) {
        digitalWrite(HEATER_RL2_PIN, HIGH);
      } else {
        digitalWrite(HEATER_RL2_PIN, LOW);
      }
    } else {
      digitalWrite(HEATER_RL1_PIN, LOW);
      digitalWrite(HEATER_RL2_PIN, LOW);
    }
  } else {
    digitalWrite(HEATER_RL1_PIN, LOW);
    digitalWrite(HEATER_RL2_PIN, LOW);
  }

  if (currentState == STATE_SENSOR_FAULT) {
    Serial.print("T:ERR,SET:");
    Serial.print(targetTemp, 1);
    Serial.print(",H:0,P:0,RAW:");
    Serial.println(lastRawADC, 1);
  } else {
    Serial.print("T:");
    Serial.print(currentTemp, 1);
    Serial.print(",SET:");
    Serial.print(targetTemp, 1);
    Serial.print(",H:");
    Serial.print(heaterEnabled ? "1" : "0");
    Serial.print(",P:0,RAW:");
    Serial.println(lastRawADC, 1);
  }

  delay(200);
}
