# BrewZilla 3.1.1 Web Controller 🍺

A custom, robust Flask/Gunicorn web interface and automation controller for the BrewZilla 3.1.1 All-in-One Homebrew System, running on a Raspberry Pi with serial communication to an Arduino Nano.

---

## Key Features

- Dual Display Modes:
  - ADVANCED View: Full modern web dashboard with multi-step mash profile programming, delayed start timer, live ADC RAW monitoring, and direct target controls.
  - CLASSIC View: Retro LCD 20x4 style simulation with physical button-like controls for seamless brewing.
- 5-Step Mash Profile Automation: Programmable multi-step mashing (Strike Heat, Mash, Mash Out, Boil Warmup, Boil) with countdown timers and automated target temperature updates.
- Delayed Start Timer: Set a specific time (e.g., 06:00 AM) to automatically start pre-heating your strike water.
- Hardware Fallback & Crash Prevention: try/except validated API commands and serial line communication prevent Gunicorn/Flask worker crashes on invalid or missing web payloads.
- Persistent Network Stability: Disables Wi-Fi power saving mode (Power save: off) to prevent SSH/Web connectivity drops during long brewing days.
- SSL / HTTPS Support: Built-in self-signed certificates for secure local network control (https://<raspberry-pi-ip>).

---

## Hardware Architecture

- SBC: Raspberry Pi 3B / 4B / Zero 2 W running Debian/Raspberry Pi OS.
- Microcontroller: Arduino Nano (ATmega328P) connected via USB Serial (/dev/ttyUSB0 @ 9600 baud).
- Relays: Dual relay outputs for Kettle Heating Element and Pump Control.
- Sensors: NTC Thermistor / Temperature Probe connected to Arduino ADC A0.

---

## Repository Structure

├── web_brewzilla.py         # Main Flask/Gunicorn Web Application & API
├── web_brewzilla_GOLDEN.py  # Verified stable production backup file
├── firmware/
│   └── firmware.ino        # Arduino Nano serial interface sketch
├── certs/                   # SSL/TLS certificates for HTTPS (Not tracked)
├── .gitignore               # Excludes secrets, certificates, and backups
├── INSTALL.md               # Hardware & replication guide
└── README.md                # Project documentation

---

## Quick Installation Guide

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

## Contributing & Replicating

Feel free to fork this project, open issues, or submit pull requests to improve the BrewZilla automation workflow!

Brewed with passion by Aguirre Brews. 🍻
