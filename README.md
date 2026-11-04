# Aguirre's BrewZilla Controller (v1.0)

The ultimate modern web-based controller for your BrewZilla 3.0, 3.1, and 3.1.1 brewing system, powered by a Raspberry Pi and Arduino.

## Overview

Aguirre's BrewZilla Controller replaces or augments the standard hardware interface with a secure, responsive web dashboard hosted locally on your Raspberry Pi. Manage your mash profiles, monitor real-time temperatures, control heating and boiling elements, and track system uptimes directly from your phone, tablet, or computer over HTTPS.

---

## Key Features

- **Modern Web Dashboard**: Single-page application interface built with Python Flask and Gunicorn, featuring real-time status polling.
- **Dual Operating Modes**:
  - **Manual Mode**: Direct control over target temperatures, heating elements, and boil modes.
  - **Auto Mode (Mash Steps Programmer)**: Multi-step automated profile scheduling with customizable strike, mash, and mashout steps, plus a **Delayed Start** timer.
- **System Uptime & Boot Monitoring**: Real-time display of Raspberry Pi OS uptime, exact boot timestamp, and web service runtime.
- **Hardware Safety & Alerts**: Integrated buzzer testing, communication loss detection with the Arduino via serial link, and anti-bounce heating protection.
- **Remote Access & Safety**: Secured via local SSL certificates (`https://`) with a built-in remote Raspberry Pi safe shutdown button.

---

## System Architecture

- **Backend**: Python 3 Flask server (`web_brewzilla.py`) running via Gunicorn and managed by `systemd`.
- **Microcontroller**: Arduino-based firmware communicating via serial (`/dev/ttyUSB0` at 9600 baud).
- **Project Directory**: `/home/pi/BrewZilla`
- **Security**: SSL certificates located at `/home/pi/BrewZilla/certs/`

---

## Hardware Pinout Reference

Make sure your Arduino is wired correctly to the BrewZilla internal relays and sensors:

| Pin | Component / Function | Description |
| :--- | :--- | :--- |
| **A0** | NTC Temperature Sensor | Analog input for brew temperature monitoring |
| **D3** | Heater Relay (RL1) | Control signal for heating elements / Boil mode |
| **D4** | Buzzer (BUZ) | Audio alerts and notifications |
| **D5** | Pump Relay (RL2) | Control signal for recirculation pump |
| **5V** | Power (VIN) | 5V power output/input for peripherals & sensors |
| **GND** | Ground (Common Node) | Common system ground |

---

## Installation & Setup

### 1. Clone or Copy the Repository
Ensure your project files are located in the home directory:
```bash
cd ~/
git clone https://github.com/aguirrebrews/BrewZilla-3.1.1-Web-Controller.git BrewZilla
cd ~/BrewZilla
```

### 2. Configure Systemd Service
To ensure the web controller starts automatically on boot as a secure background service, verify or create your service file at `/etc/systemd/system/brewzilla-web.service`:

```ini
[Unit]
Description=BrewZilla Web Controller Service
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/BrewZilla
ExecStart=/usr/bin/gunicorn --workers 1 --threads 4 --bind 0.0.0.0:443 --keyfile /home/pi/BrewZilla/certs/brewzilla.local+3-key.pem --certfile /home/pi/BrewZilla/certs/brewzilla.local+3.pem web_brewzilla:app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable brewzilla-web
sudo systemctl restart brewzilla-web
```

---

## Workflow & Deployment

When updating code or making adjustments to `web_brewzilla.py`:
1. Edit the file (via WinSCP or your preferred text editor).
2. Verify Python syntax before deploying:
   ```bash
   python3 -m py_compile ~/BrewZilla/web_brewzilla.py
   ```
3. Restart the service to apply changes:
   ```bash
   sudo systemctl restart brewzilla-web
   ```
4. Check service health:
   ```bash
   sudo systemctl status brewzilla-web --no-pager
   ```

---

## Troubleshooting

- **Check Serial Connection**: Ensure the Arduino is properly connected to `/dev/ttyUSB0`:
  ```bash
  ls -l /dev/ttyUSB0
  ```
- **Inspect Service Logs**: If the web panel is unreachable, check system logs for errors:
  ```bash
  sudo journalctl -u brewzilla-web -f
  ```
