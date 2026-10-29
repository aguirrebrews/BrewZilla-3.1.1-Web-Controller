# BrewZilla 3.1.1 Web Controller v0.9.1 🍺

A custom, robust Flask/Gunicorn web interface and automation controller for the BrewZilla 3.1.1 All-in-One Homebrew System, running on a Raspberry Pi with serial communication to an Arduino Nano.

---

## 💡 About This Project & Acknowledgments

This project represents a complete transformation and modern overhaul of the original factory controller for the BrewZilla 3.1.1. The original concept and a significant portion of the foundational codebase were derived from the open-source project by BetterRobotics (https://github.com/BetterRobotics). We extend our sincere gratitude and appreciation to the BetterRobotics team for providing the initial inspiration, framework, and codebase that made this effort possible.

Over time, however, the software architecture, safety protocols, user interface, and hardware integration have been substantially rewritten, optimized, and expanded. It has evolved into a fully independent, standalone homebrew automation system designed specifically for high operational reliability, precise thermal control, and secure web access.

---

## 🛠 Required Equipment & Minimalist Hardware Setup

One of the main advantages of this project is its minimalist hardware footprint. You do not need extra power relays, solid-state relays (SSRs), or external power control modules, as the software hooks directly into the native internal relays, NTC temperature probe, and buzzer built into the BrewZilla unit.

### 🛒 Equipment List

1. Single-Board Computer (SBC): Raspberry Pi 3B, 4B, or Zero 2 W running Debian/Raspberry Pi OS.
2. Microcontroller: Arduino Nano (ATmega328P).
3. Screw Terminal Expansion Shield: Pre-soldered breakout board for Arduino Nano (allows clean, reliable screw-terminal wire hookups without soldering directly to the MCU).
4. Jumper Wires: Dupont jumper wires (Female-to-Female / Male-to-Female).
5. USB Cable: USB-A to Mini-USB data cable (connecting Raspberry Pi to Arduino Nano).
6. BrewZilla 3.1.1 System: Uses native internal heating elements, internal relays, NTC probe, and passive buzzer.

---

## ✨ Key Features

- Dual Display Modes:
  - ADVANCED View: Modern web dashboard with multi-step mash profile programming, delayed start timer, live ADC RAW monitoring, and direct target controls.
  - CLASSIC View: Retro LCD 20x4 style simulation with physical button-like controls for seamless brewing.
- 5-Step Mash Profile Automation: Programmable multi-step mashing (Strike Heat, Mash, Mash Out, Boil Warmup, Boil) with countdown timers and automated target temperature updates.
- Delayed Start Timer: Set a specific time (e.g., 06:00 AM) to automatically start pre-heating your strike water.
- Hardware Fail-Safe & Watchdog Protection: Embedded AVR Watchdog timer (2s) and serial heartbeat logic (30s) instantly cut power to heating elements if the web application or serial link disconnects.
- Persistent Network Stability: Disables Wi-Fi power-saving mode (Power save: off) to prevent SSH/Web connectivity drops during long brewing days.
- SSL / HTTPS Support: Built-in self-signed certificates for secure local network control (https://<raspberry-pi-ip>).

---

## 📐 Hardware Architecture

- SBC: Raspberry Pi 3B / 4B / Zero 2 W running Debian/Raspberry Pi OS.
- Microcontroller: Arduino Nano (ATmega328P) connected via USB Serial (/dev/ttyUSB0 @ 9600 baud).
- Expansion Board: Pre-soldered Arduino Nano screw terminal breakout board.
- Relays: BrewZilla native internal dual relay outputs for kettle heating elements.
- Sensors: BrewZilla native NTC Thermistor / Temperature Probe connected to Arduino ADC A0.

---

## 📁 Repository Structure

├── web_brewzilla.py         # Main Flask/Gunicorn Web Application & API
├── web_brewzilla_GOLDEN.py  # Verified stable production backup file
├── firmware/
│   └── firmware.ino        # Arduino Nano serial interface sketch
├── certs/                   # SSL/TLS certificates for HTTPS (Not tracked)
├── .gitignore               # Excludes secrets, certificates, and backups
├── INSTALL.md               # Hardware & replication guide
└── README.txt               # Project documentation

---

## 🚀 Quick Installation Guide

For detailed hardware wiring and step-by-step setup instructions, please see INSTALL.md.

1. Clone the repository:
   git clone git@github.com:aguirrebrews/BrewZilla-3.1.1-Web-Controller.git ~/BrewZilla
   cd ~/BrewZilla

2. Install Python Dependencies:
   sudo apt update
   sudo apt install -y python3-flask python3-serial gunicorn

3. Configure Systemd Web Service:
   sudo cp systemd/brewzilla-web.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable brewzilla-web
   sudo systemctl start brewzilla-web

4. Access the Web Interface:
   Open your browser and navigate to https://<YOUR_PI_IP> (e.g., https://192.168.68.5).

---

## 🤝 Contributing & Replicating

Feel free to fork this project, open issues, or submit pull requests to improve the BrewZilla automation workflow!

Special thanks to BetterRobotics (https://github.com/BetterRobotics) for inspiring the original foundation of this work. 🍻
