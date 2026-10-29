import threading
import time
import json
import serial
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

state = {
    "connected": False,
    "temp_actual": 0.0,
    "temp_objetivo": 163.0,
    "heater": False,
    "pump": False,
    "boil_mode": False,
    "mode": "MANUAL",
    "ui_view": "CLASSIC",
    "last_update": "",
    "raw": 0,
    "sequence_active": False,
    "current_step": 0,
    "step_time_remaining": 0,
    "steps": [
        {"name": "Step 1 (Pre-soak)", "temp": 32.0, "hours": 12, "mins": 0, "enabled": True},
        {"name": "Step 2 (Strike Heat)", "temp": 163.0, "hours": 2, "mins": 0, "enabled": True},
        {"name": "Step 3 (Mash)", "temp": 152.0, "hours": 1, "mins": 0, "enabled": False},
        {"name": "Step 4 (Mash Out)", "temp": 170.0, "hours": 0, "mins": 10, "enabled": False},
        {"name": "Step 5 (Boil Warmup)", "temp": 208.0, "hours": 0, "mins": 0, "enabled": False},
        {"name": "Step 6 (Boil)", "temp": 212.0, "hours": 1, "mins": 0, "enabled": False}
    ]
}

ser = None

def serial_loop():
    global ser, state
    while True:
        if ser is None or not ser.is_open:
            try:
                ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
                state["connected"] = True
            except Exception:
                state["connected"] = False
                time.sleep(2)
                continue

        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                state["last_update"] = time.strftime("%H:%M:%S")
                state["connected"] = True
                parts = line.split(',')
                for part in parts:
                    if ':' in part:
                        k, v = part.split(':', 1)
                        if k == 'T': 
                            state["temp_actual"] = float(v)
                        elif k == 'SET': 
                            state["temp_objetivo"] = float(v)
                        elif k == 'H': 
                            if v == 'H':
                                state["heater"] = True
                                state["boil_mode"] = True
                            else:
                                state["heater"] = (v == '1')
                        elif k == 'P': 
                            state["pump"] = (v == '1')
                        elif k == 'RAW': 
                            state["raw"] = float(v)
        except Exception:
            state["connected"] = False
            if ser:
                try:
                    ser.close()
                except Exception:
                    pass
            ser = None
            time.sleep(1)

# Iniciar hilo de comunicacion serial en segundo plano
t_serial = threading.Thread(target=serial_loop, daemon=True)
t_serial.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aguirre's BrewZilla Controller</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; text-align: center; margin: 0; padding: 20px; }
        .status-bar { display: flex; justify-content: space-between; font-size: 1.1em; margin-bottom: 20px; font-weight: bold; background: #1e1e1e; padding: 15px; border-radius: 8px; }
        .connected { color: #4caf50; }
        .disconnected { color: #f44336; }
        #clock { color: #aaa; }
        .panel { background: #1e1e1e; padding: 25px; border-radius: 12px; max-width: 650px; margin: auto; box-shadow: 0px 4px 15px rgba(0,0,0,0.5); }
        .btn { padding: 15px 25px; font-size: 1.1em; margin: 5px; cursor: pointer; border: none; border-radius: 5px; color: white; font-weight: bold; transition: 0.2s; }
        .btn:active { transform: scale(0.95); }
        .btn-on { background-color: #4caf50; }
        .btn-off { background-color: #f44336; }
        .btn-blue { background-color: #2196f3; }
        .btn-orange { background-color: #ff9800; }
        .input-group { margin: 20px 0; }
        input[type="number"] { padding: 12px; font-size: 1.2em; width: 120px; text-align: center; border-radius: 5px; border: none; background: #333; color: white; }
        .controls-grid { display: flex; justify-content: center; flex-wrap: wrap; gap: 15px; margin-top: 20px; }
        .control-box { border: 1px solid #333; padding: 15px; border-radius: 8px; background: #252525; }
        .control-box h4 { margin: 0 0 15px 0; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="panel">
        <div class="status-bar">
            <span id="conn-status" class="disconnected">Arduino: Buscando...</span>
            <span id="clock">--:--:--</span>
        </div>
        <h1 style="color: #ff9800; margin-bottom: 5px;">Aguirre's BrewZilla Controller</h1>
        <div style="margin-bottom: 25px; color: #888; font-size: 0.95em;">
            RAW ADC: <span id="raw-adc">--</span> | Logica Calentador: <span id="heater-state">--</span>
        </div>
        <div style="display: flex; gap: 15px; justify-content: center; margin-bottom: 25px;">
            <div style="flex: 1; background: #252525; padding: 15px; border-radius: 8px; border: 1px solid #333; text-align: center;">
                <h4 style="margin: 0 0 5px 0; color: #aaa; font-size: 13px;">CURRENT TEMP</h4>
                <div style="font-size: 36px; font-weight: bold; color: #00ffcc;"><span id="current-temp">--</span> &deg;F</div>
            </div>
            <div style="flex: 1; background: #252525; padding: 15px; border-radius: 8px; border: 1px solid #333; text-align: center;">
                <h4 style="margin: 0 0 5px 0; color: #aaa; font-size: 13px;">CURRENT SET</h4>
                <div style="font-size: 36px; font-weight: bold; color: #ff9900;"><span id="target-temp">--</span> &deg;F</div>
            </div>
        </div>
        <div class="input-group">
            <input type="number" id="target-input" placeholder="Temp F" step="0.5">
            <button class="btn btn-blue" onclick="setTarget()">Fijar Target</button>
        </div>
        <div class="controls-grid">
            <div class="control-box" style="border-color: #ff9800;">
                <h4 style="color: #ff9800;">Buzzer (Test)</h4>
                <button class="btn btn-on" onclick="toggleCmd('BEEP')">ON</button>
            </div>
            <div class="control-box">
                <h4>Calentadores</h4>
                <button class="btn btn-on" onclick="toggleCmd('HEATER')">AUTO</button>
                <button class="btn btn-off" onclick="toggleCmd('HEATER')">OFF</button>
                <button class="btn btn-orange" onclick="toggleBoil()">BOIL</button>
            </div>
        </div>
    </div>
    <script>
        setInterval(() => {
            const now = new Date();
            document.getElementById('clock').innerText = now.toLocaleTimeString('en-US', {
                hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true
            });
        }, 1000);

        function updateStatus() {
            fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    const nowStr = new Date().toLocaleTimeString('en-US', {
                        hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true
                    });
                    const connEl = document.getElementById('conn-status');
                    if (data.connected) {
                        connEl.innerText = 'Arduino: Conectado (' + nowStr + ')';
                        connEl.className = 'connected';
                    } else {
                        connEl.innerText = 'Arduino: Desconectado (' + nowStr + ')';
                        connEl.className = 'disconnected';
                    }
                    document.getElementById('current-temp').innerText = data.temp_actual.toFixed(1);
                    document.getElementById('target-temp').innerText = data.temp_objetivo.toFixed(1);
                    document.getElementById('raw-adc').innerText = data.raw;

                    let hState = "OFF";
                    if(data.boil_mode) hState = "BOIL MODE";
                    else if(data.heater) hState = "AUTO";
                    document.getElementById('heater-state').innerText = hState;
                });
        }

        function setTarget() {
            const val = parseFloat(document.getElementById('target-input').value);
            if(!isNaN(val)) {
                fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'SET_TEMP', value: val})
                });
            }
        }

        function toggleBoil() {
            fetch('/api/boil/toggle', {method: 'POST'});
        }

        function toggleCmd(target) {
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'TOGGLE', target: target})
            });
        }

        setInterval(updateStatus, 1000);
        updateStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    return jsonify(state)

@app.route('/api/boil/toggle', methods=['POST'])
def toggle_boil():
    global ser, state
    state["boil_mode"] = not state["boil_mode"]
    if state["boil_mode"]:
        state["heater"] = True
        cmd = "H:H\n"
    else:
        state["heater"] = False
        cmd = "H:0\n"
    
    if ser and ser.is_open:
        try:
            ser.write(cmd.encode('utf-8'))
        except Exception:
            pass
    return jsonify({"success": True, "boil_mode": state["boil_mode"], "heater": state["heater"]})

@app.route('/api/command', methods=['POST'])
def send_command():
    global ser, state
    data = request.get_json() or {}
    cmd = ""
    action = data.get("action")

    if action == "TOGGLE":
        target = data.get("target")
        if target == "HEATER":
            state["heater"] = not state["heater"]
            if not state["heater"]:
                state["boil_mode"] = False
            cmd = f"H:{1 if state['heater'] else 0}\n"
        elif target == "BEEP":
            cmd = "BEEP\n"
    elif action == "SET_TEMP":
        val = data.get("value", 163.0)
        try:
            state["temp_objetivo"] = float(val)
            cmd = f"SET:{state['temp_objetivo']:.1f}\n"
        except Exception:
            pass

    if ser and ser.is_open and cmd:
        try:
            ser.write(cmd.encode('utf-8'))
            ser.flush()
        except Exception as e:
            print("Error serial:", e)

    return jsonify({"success": True, "state": state})

if __name__ == '__main__':
    cert_path = '/home/pi/BrewZilla/certs/brewzilla.local+3.pem'
    key_path = '/home/pi/BrewZilla/certs/brewzilla.local+3-key.pem'
    app.run(host='0.0.0.0', port=443, ssl_context=(cert_path, key_path), debug=False)