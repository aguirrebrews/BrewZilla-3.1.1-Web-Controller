# Complete Replication & Setup Guide for BrewZilla 3.1.1

This guide provides step-by-step instructions to replicate the hardware setup, flash the Arduino microcontroller, and configure the Raspberry Pi web server.

---

## 1. Hardware Requirements & Wiring

| Component | Connection / Pin | Notes |
| :--- | :--- | :--- |
| Arduino Nano | USB Port | Connected to Pi via /dev/ttyUSB0 |
| Temp Sensor | Analog Pin A0 | NTC Thermistor / Analog Probe |
| Heater Relay 1 | Digital Pin D3 | Primary Heating Element |
| Buzzer | Digital Pin D4 | Target Temp & Step Alerts |
| Heater Relay 2 | Digital Pin D5 | Secondary Element / Boil Mode |

---

## 2. Flashing the Arduino Firmware

Ensure arduino-cli is installed on your Raspberry Pi, or upload firmware/firmware.ino using the official Arduino IDE on your PC:

arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328 ~/BrewZilla/firmware/firmware.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano:cpu=atmega328 ~/BrewZilla/firmware/firmware.ino

---

## 3. Raspberry Pi Wi-Fi Power Management Fix

To prevent SSH or Web disconnects during long mashing/boil sessions:

sudo iwconfig wlan0 power off
(crontab -l 2>/dev/null; echo "@reboot /sbin/iwconfig wlan0 power off") | crontab -

---

## 4. Setting up Gunicorn & SSL Certificates

Generate self-signed SSL certificates using openssl:

mkdir -p ~/BrewZilla/certs
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout ~/BrewZilla/certs/brewzilla.local+3-key.pem \
  -out ~/BrewZilla/certs/brewzilla.local+3.pem \
  -subj "/CN=brewzilla.local"

Verify service status:
sudo systemctl status brewzilla-web
