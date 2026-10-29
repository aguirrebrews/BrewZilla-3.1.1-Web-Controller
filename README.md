# BrewZilla 3.1.1 Web Controller v0.9.1 🍺

A custom, robust Flask/Gunicorn web interface and automation controller for the **BrewZilla 3.1.1 All-in-One Homebrew System**, running on a Raspberry Pi with serial communication to an Arduino Nano.

---

## 💡 About This Project & Acknowledgments

This project represents a complete transformation and modern overhaul of the original factory controller for the **BrewZilla 3.1.1**. The original concept and a significant portion of the foundational code were derived from the open-source project by [BetterRobotics](https://github.com/BetterRobotics). We extend our sincere gratitude and appreciation to the BetterRobotics team for providing the initial inspiration, framework, and codebase that made this effort possible.

Over time, however, the software architecture, safety protocols, user interface, and hardware integration have been substantially rewritten, optimized, and expanded. It has evolved into a fully independent, standalone homebrew automation system designed specifically for high operational reliability, precise thermal control, and secure web access.

---

## 🛠 What This Project Represents & Does

The **BrewZilla 3.1.1 Web Controller** bypasses the original factory panel to provide a high-performance **SBC (Raspberry Pi) + Microcontroller (Arduino Nano)** hybrid control system:

- **Hardware Fail-Safe & Watchdog Protection:** Uses an AVR Watchdog timer and serial heartbeat mechanism to instantly cut power to heating elements if the web application or network connection drops.
- **Precision Thermal Control:** Reads the kettle's original NTC probe through custom piecewise linear calibration and hysteresis logic to eliminate temperature overshoot during mashing.
- **Automated Multi-Step Mashing:** Features a fully programmable 5-step mash profile (*Strike Heat, Mash, Mash Out, Boil Warmup, Boil*) with target updates, step countdowns, and audible alerts.
- **Delayed Start Timer:** Allows brewers to schedule an automatic pre-heating time (e.g., `06:00 AM`) so strike water is ready as soon as the brew day begins.
- **Dual Display Modes (HTTPS):**
  - **ADVANCED View:** Modern interactive web dashboard with live ADC RAW telemetries, progress spinners, temperature target setters, and system status indicators.
  - **CLASSIC View:** Nostalgic LCD 20x4 simulation with physical button-like navigation.
- **Production-Grade Web Server:** Runs on Flask + Gunicorn WSGI managed by Systemd over HTTPS (Port 443), with automatic Wi-Fi power-saving disabling to prevent connection drops during long brew sessions.

---

## Key Features

- **Dual Display Modes:**
  - **ADVANCED View:** Full modern web dashboard with multi-step mash profile programming, delayed start timer, live ADC RAW monitoring, and direct target controls.
  - **CLASSIC View:** Retro LCD 20x4 style simulation with physical button-like controls for seamless brewing.
- **5-Step Mash Profile Automation:** Programmable multi-step mashing (Strike Heat, Mash, Mash Out, Boil Warmup, Boil) with countdown timers and automated target temperature updates.
- **Delayed Start Timer:** Set a specific time (e.g., `06:00 AM`) to automatically start pre-heating your strike water.
- **Hardware Fallback & Crash Prevention:** `try/except` validated API commands and serial line communication prevent Gunicorn/Flask worker crashes on invalid or missing web payloads.
- **Persistent Network Stability:** Disables Wi-Fi power saving mode (`Power save: off`) to prevent SSH/Web connectivity drops during long brewing days.
- **SSL / HTTPS Support:** Built-in self-signed certificates for secure local network control (`https://<raspberry-pi-ip>`).

---

## Hardware Architecture

- **SBC:** Raspberry Pi 3B / 4B / Zero 2 W running Debian/Raspberry Pi OS.
- **Microcontroller:** Arduino Nano (ATmega328P) connected via USB Serial (`/dev/ttyUSB0
