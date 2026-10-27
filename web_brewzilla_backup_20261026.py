import os
import threading
import time
import serial
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Estado global del sistema
state = {
    "connected": False,
    "temp_actual": 0.0,
    "temp_objetivo": 163.0,
    "heater": False,
    "pump": False,
    "boil_mode": False,
    "mode": "MANUAL",
    "ui_view": "ADVANCED",
    "last_update": "",
    "raw": 0,
    "sequence_active": False,
    "current_step": 0,
    "step_time_remaining": 0,
    "step_total_time": 0,
    "delayed_start_enabled": False,
    "delayed_start_time": "06:00",
    "waiting_for_delay": False,
    "steps": [
        {"name": "Step 1 (Strike Heat)", "temp": 163.0, "hours": 2, "mins": 0, "enabled": True},
        {"name": "Step 2 (Mash)", "temp": 152.0, "hours": 1, "mins": 0, "enabled": True},
        {"name": "Step 3 (Mash Out)", "temp": 170.0, "hours": 0, "mins": 30, "enabled": True},
        {"name": "Step 4 (Boil Warmup)", "temp": 208.0, "hours": 0, "mins": 0, "enabled": False},
        {"name": "Step 5 (Boil)", "temp": 212.0, "hours": 1, "mins": 0, "enabled": False}
    ]
}

ser = None

def serial_loop():
    global ser, state
    last_ping_time = time.time()
    
    while True:
        if ser is None or not ser.is_open:
            try:
                ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
                state["connected"] = True
            except Exception:
                state["connected"] = False
                time.sleep(2)
                continue

        if time.time() - last_ping_time >= 5:
            last_ping_time = time.time()
            if ser and ser.is_open:
                try:
                    ser.write(b"PING\n")
                except Exception:
                    pass

        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                state["last_update"] = time.strftime("%H:%M:%S")
                parts = line.split(',')
                for part in parts:
                    if ':' in part:
                        k, v = part.split(':', 1)
                        try:
                            if k == 'T': state["temp_actual"] = float(v)
                            elif k == 'SET': state["temp_objetivo"] = float(v)
                            elif k == 'H':
                                if v == 'H':
                                    state["heater"] = True
                                    state["boil_mode"] = True
                                else:
                                    state["heater"] = (v == '1')
                            elif k == 'P': state["pump"] = (v == '1')
                            elif k == 'RAW': state["raw"] = float(v)
                        except ValueError:
                            pass
        except Exception:
            state["connected"] = False
            if ser:
                try:
                    ser.close()
                except Exception:
                    pass
            ser = None
            time.sleep(1)

def sequence_loop():
    global state, ser
    while True:
        time.sleep(1)
        if state["sequence_active"]:
            
            if state["waiting_for_delay"]:
                current_time_str = time.strftime("%H:%M")
                if current_time_str == state["delayed_start_time"]:
                    state["waiting_for_delay"] = False
                    state["heater"] = True
                    if ser and ser.is_open:
                        try:
                            ser.write(b"H:1\n") # <-- AQUÍ SE ENCIENDE EL CALENTADOR A LA HORA PROGRAMADA
                        except Exception:
                            pass
                else:
                    if state["heater"]:
                        state["heater"] = False
                        if ser and ser.is_open:
                            try:
                                ser.write(b"H:0\n")
                            except Exception:
                                pass
                    continue

            step_idx = state["current_step"]
            if step_idx < len(state["steps"]):
                current_s = state["steps"][step_idx]
                if not current_s["enabled"]:
                    state["current_step"] += 1
                    if state["current_step"] < len(state["steps"]):
                        next_s = state["steps"][state["current_step"]]
                        state["step_total_time"] = (next_s["hours"] * 3600) + (next_s["mins"] * 60)
                        state["step_time_remaining"] = state["step_total_time"]
                    continue

                if state["temp_objetivo"] != current_s["temp"]:
                    state["temp_objetivo"] = current_s["temp"]
                    if ser and ser.is_open:
                        try:
                            ser.write(f"SET:{current_s['temp']}\n".encode('utf-8'))
                        except Exception:
                            pass

                if state["step_time_remaining"] > 0:
                    state["step_time_remaining"] -= 1
                else:
                    if ser and ser.is_open:
                        try:
                            ser.write(b"CHINGATU\n")
                        except Exception:
                            pass

                    state["current_step"] += 1
                    if state["current_step"] < len(state["steps"]):
                        next_s = state["steps"][state["current_step"]]
                        state["step_total_time"] = (next_s["hours"] * 3600) + (next_s["mins"] * 60)
                        state["step_time_remaining"] = state["step_total_time"]
                    else:
                        state["sequence_active"] = False
            else:
                state["sequence_active"] = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aguirre's Brewzilla Controller</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #121212; color: #fff; text-align: center; margin: 0; padding: 15px; }
        .logo-container { margin: 5px auto; max-width: 75px; }
        .logo-img { width: 100%; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 8px rgba(255,255,255,0.3); }
        h1 { font-size: 1.1rem; letter-spacing: 0.8px; margin: 5px 0; color: #e0e0e0; text-transform: uppercase; }
        .status-container { margin: 3px auto 12px auto; max-width: 450px; }
        .status { font-size: 0.8rem; padding: 3px 8px; border-radius: 15px; display: inline-block; font-weight: bold; }
        .online { background: #2e7d32; color: #fff; }
        .offline { background: #c62828; color: #fff; }
        .meta-info { margin-top: 4px; font-size: 0.85rem; color: #aaa; font-weight: 500; }
        .card { background: #1e1e1e; border-radius: 12px; padding: 18px; margin: 12px auto; max-width: 450px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        
        .temp-display-box {
            display: flex;
            justify-content: space-around;
            align-items: center;
            background: #252525;
            padding: 12px;
            border-radius: 10px;
            margin: 8px 0 12px 0;
            border: 1px solid #333;
        }
        .temp-col { flex: 1; }
        .temp-label { font-size: 0.75rem; color: #aaa; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
        .temp-val { font-size: 2rem; font-weight: bold; margin-top: 2px; }
        .temp-actual-color { color: #ff9800; }
        .temp-target-color { color: #2196f3; }
        .temp-divider { border-left: 1px solid #444; height: 40px; }

        .btn { width: 100%; padding: 12px; border: 1px solid #333; border-radius: 8px; font-size: 1rem; font-weight: bold; margin: 5px 0; cursor: pointer; transition: 0.2s; color: #aaa; background: #161616; }
        .btn-heater.active { background: #d32f2f; color: #fff; border-color: #ff5252; box-shadow: 0 0 15px #ff5252; }
        .btn-boil.active { background: #d32f2f; color: #fff; border-color: #ff5252; box-shadow: 0 0 15px #ff5252; }
        .btn-mode { background: #161616; color: #aaa; }
        .btn-mode.auto { background: #00897b; color: #fff; border-color: #26a69a; box-shadow: 0 0 12px #00897b; }
        .btn-view { background: #37474f; color: #fff; border-color: #546e7a; padding: 10px; font-size: 0.9rem; }
        .btn-shutdown { background: #b71c1c; color: #fff; border-color: #f44336; padding: 10px; font-size: 0.9rem; }
        .btn-start { background: #2e7d32; color: #fff; border: none; }
        .btn-stop { background: #c62828; color: #fff; border: none; }
        input[type=number], input[type=time] { padding: 5px; font-size: 0.95rem; border-radius: 6px; border: none; text-align: center; background: #333; color: #fff; }
        .target-row { margin: 6px 0; display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }

        .classic-panel {
            background: #111; border: 4px solid #333; border-radius: 30px; padding: 20px;
            max-width: 600px; margin: 15px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            display: flex; align-items: center; justify-content: space-between;
        }
        .classic-side { display: flex; flex-direction: column; gap: 10px; width: 85px; }
        .c-btn {
            background: #1e1e1e; color: #fff; border: 2px solid #444; border-radius: 12px;
            padding: 10px 4px; font-size: 0.75rem; font-weight: bold; cursor: pointer; transition: 0.1s;
        }
        .c-btn:active { background: #333; transform: scale(0.95); }
        .lcd-screen {
            background: #0055ff; color: #d6f5ff; border: 4px solid #002288; border-radius: 10px;
            width: 280px; height: 160px; padding: 12px; display: flex; flex-direction: column;
            justify-content: space-between; box-shadow: inset 0 0 20px rgba(0,0,0,0.6);
            font-family: monospace; text-shadow: 0 0 5px rgba(214,245,255,0.8);
        }
        .lcd-top { display: flex; justify-content: space-between; font-size: 1rem; font-weight: bold; }
        .lcd-mid { display: flex; justify-content: space-around; align-items: center; font-size: 1.6rem; font-weight: bold; }
        .lcd-bot { display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: bold; }

        .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,152,0,0.3); border-top-color: #ff9800; border-radius: 50%; animation: win7-spin 0.8s linear infinite; vertical-align: middle; }
        @keyframes win7-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .hidden { display: none !important; }
        table { width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 0.85rem; }
        th, td { padding: 6px; border-bottom: 1px solid #333; }
        
        .delay-box { background: #2a2a2a; border-radius: 8px; padding: 10px; margin: 10px 0 12px 0; border: 1px solid #444; text-align: left; }
    </style>
</head>
<body>
    <div class="logo-container">
        <img class="logo-img" src="/static/logo.png" alt="BrewZilla Logo">
    </div>
    <h1>AGUIRRE'S BREWZILLA CONTROLLER</h1>

    <div class="status-container">
        <span id="conn-status" class="status offline">Arduino Disconnected</span>
        <div class="meta-info">
            <span id="clock">--:--:-- --</span> | RAW ADC: <span id="raw-adc">--</span>
        </div>
    </div>

    <div style="margin: 5px auto 10px auto; max-width: 450px;">
        <button id="btn-view" class="btn btn-view" onclick="toggleView()">SWITCH TO CLASSIC VIEW</button>
        <button class="btn btn-shutdown" onclick="shutdownPi()">🔴 SHUTDOWN PI</button>
    </div>

    <div id="view-normal">
        <div class="card">
            <div class="temp-display-box">
                <div class="temp-col">
                    <div class="temp-label">Current Temp</div>
                    <div class="temp-val temp-actual-color"><span id="temp-val-adv">---.-</span> °F</div>
                </div>
                <div class="temp-divider"></div>
                <div class="temp-col">
                    <div class="temp-label">Set Temp</div>
                    <div class="temp-val temp-target-color"><span id="temp-set-adv">---.-</span> °F</div>
                </div>
            </div>

            <div style="text-align: left; background: #252525; padding: 12px; border-radius: 8px; margin-top: 10px;">
                <div class="target-row">
                    <span>Strike Target:</span>
                    <div>
                        <input type="number" id="target-strike" value="163" step="0.5" style="width: 55px;"> °F
                        <button onclick="setTarget(163, 'spinner-strike')" style="padding: 5px 8px; background: #ff9800; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; color: #fff;">SET</button>
                        <span id="spinner-strike" class="spinner hidden" style="margin-left: 5px;"></span>
                    </div>
                </div>
                <div class="target-row">
                    <span>Mash Target:</span>
                    <div>
                        <input type="number" id="target-mash" value="152" step="0.5" style="width: 55px;"> °F
                        <button onclick="setTarget(152, 'spinner-mash')" style="padding: 5px 8px; background: #ff9800; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; color: #fff;">SET</button>
                        <span id="spinner-mash" class="spinner hidden" style="margin-left: 5px;"></span>
                    </div>
                </div>
                <div class="target-row">
                    <span>Mashout Target:</span>
                    <div>
                        <input type="number" id="target-mashout" value="170" step="0.5" style="width: 55px;"> °F
                        <button onclick="setTarget(170, 'spinner-mashout')" style="padding: 5px 8px; background: #ff9800; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; color: #fff;">SET</button>
                        <span id="spinner-mashout" class="spinner hidden" style="margin-left: 5px;"></span>
                    </div>
                </div>
            </div>

            <button id="btn-boil" class="btn btn-boil" onclick="toggleBoil()" style="margin-top: 10px;">BOIL MODE: OFF</button>
        </div>

        <div class="card">
            <button id="btn-heater" class="btn btn-heater" onclick="toggleCmd('HEATER')">HEATER: OFF</button>
            <button id="btn-mode" class="btn btn-mode" onclick="toggleMode()">MODE: MANUAL</button>
        </div>

        <div id="card-programmer" class="card hidden">
            <h3>MASH STEPS PROGRAMMER</h3>
            
            <p style="margin: 6px 0;">Status: <b id="seq-status">Inactive</b></p>
            <p style="margin: 4px 0; font-size: 0.95rem; color: #2196f3;">Current Step: <b id="seq-step-info">--</b></p>
            <p style="margin: 4px 0; font-size: 0.9rem; color: #aaa;">Elapsed: <b id="seq-elapsed">[00:00:00 / 00:00:00]</b></p>
            <p style="margin: 4px 0 6px 0; font-size: 0.9rem; color: #ff9800;">Time Left: <b id="seq-timer">00:00:00</b></p>
            
            <div class="delay-box">
                <label style="font-size: 0.9rem; font-weight: bold; cursor: pointer;">
                    <input type="checkbox" id="chk-delay" onchange="toggleDelay(this.checked)"> Enable Delayed Start
                </label>
                <div style="margin-top: 6px; font-size: 0.85rem; color: #bbb;">
                    Start Heating At: 
                    <input type="time" id="time-delay" value="06:00" onchange="updateDelayTime(this.value)">
                </div>
            </div>

            <button id="btn-seq" class="btn btn-start" onclick="toggleSequence()">START MASH PROFILE</button>

            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Enable</th>
                        <th style="width: 20px;"></th>
                        <th>Target (°F)</th>
                        <th>Hours</th>
                        <th>Mins</th>
                    </tr>
                </thead>
                <tbody id="steps-table">
                </tbody>
            </table>
        </div>
    </div>

    <div id="view-classic" class="hidden">
        <div class="classic-panel">
            <div class="classic-side">
                <button class="c-btn" onclick="toggleCmd('HEATER')">⏻ POWER</button>
                <button class="c-btn" onclick="setTarget(163, 'none')">🌡 TEMP</button>
                <button class="c-btn" onclick="toggleSequence()">⏱ TIME</button>
                <button class="c-btn" onclick="toggleMode()">⚙ AUTO/MAN</button>
            </div>

            <div class="lcd-screen">
                <div class="lcd-top">
                    <span id="lcd-step">S1</span>
                    <span id="lcd-timer">00:00</span>
                </div>
                <div class="lcd-mid">
                    <div><span id="lcd-temp-target">67</span>°</div>
                    <div><span id="lcd-temp-actual">18</span>°C</div>
                </div>
                <div class="lcd-bot">
                    <span id="lcd-mode">AUTO</span>
                    <span id="lcd-state">⏸</span>
                </div>
            </div>

            <div class="classic-side">
                <button class="c-btn" onclick="adjustTemp(1)">➕ UP</button>
                <button class="c-btn" onclick="adjustTemp(-1)">➖ DOWN</button>
                <button class="c-btn" onclick="toggleBoil()">♨ S1-S6</button>
                <button class="c-btn" onclick="toggleSequence()">▶/⏸ RUN</button>
            </div>
        </div>
    </div>

    <script>
        let currentView = 'ADVANCED';

        function formatTime(totalSec) {
            const h = Math.floor(totalSec / 3600).toString().padStart(2, '0');
            const m = Math.floor((totalSec % 3600) / 60).toString().padStart(2, '0');
            const s = (totalSec % 60).toString().padStart(2, '0');
            return h + ':' + m + ':' + s;
        }

        setInterval(() => {
            const now = new Date();
            document.getElementById('clock').innerText = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
        }, 1000);

        function updateStatus() {
            fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('temp-val-adv').innerText = data.temp_actual.toFixed(1);
                    document.getElementById('temp-set-adv').innerText = data.temp_objetivo.toFixed(1);
                    document.getElementById('raw-adc').innerText = data.raw;

                    const valStrike = parseFloat(document.getElementById('target-strike')?.value || 163);
                    const valMash = parseFloat(document.getElementById('target-mash')?.value || 152);
                    const valMashout = parseFloat(document.getElementById('target-mashout')?.value || 170);

                    const spStrike = document.getElementById('spinner-strike');
                    const spMash = document.getElementById('spinner-mash');
                    const spMashout = document.getElementById('spinner-mashout');

                    if (data.heater) {
                        if (Math.abs(data.temp_objetivo - valStrike) < 0.5) spStrike?.classList.remove('hidden'); else spStrike?.classList.add('hidden');
                        if (Math.abs(data.temp_objetivo - valMash) < 0.5) spMash?.classList.remove('hidden'); else spMash?.classList.add('hidden');
                        if (Math.abs(data.temp_objetivo - valMashout) < 0.5) spMashout?.classList.remove('hidden'); else spMashout?.classList.add('hidden');
                    } else {
                        spStrike?.classList.add('hidden');
                        spMash?.classList.add('hidden');
                        spMashout?.classList.add('hidden');
                    }

                    const conn = document.getElementById('conn-status');
                    if (data.connected) {
                        conn.innerText = 'Arduino Connected (' + data.last_update + ')';
                        conn.className = 'status online';
                    } else {
                        conn.innerText = 'Arduino Disconnected';
                        conn.className = 'status offline';
                    }

                    const bH = document.getElementById('btn-heater');
                    bH.innerText = 'HEATER: ' + (data.heater ? 'ON' : 'OFF');
                    bH.className = data.heater ? 'btn btn-heater active' : 'btn btn-heater';

                    const bB = document.getElementById('btn-boil');
                    bB.innerText = 'BOIL MODE: ' + (data.boil_mode ? 'ON (212.0°F)' : 'OFF');
                    bB.className = data.boil_mode ? 'btn btn-boil active' : 'btn btn-boil';

                    const bM = document.getElementById('btn-mode');
                    bM.innerText = 'MODE: ' + data.mode;
                    bM.className = data.mode === 'AUTO' ? 'btn btn-mode auto' : 'btn btn-mode';

                    const cardProg = document.getElementById('card-programmer');
                    if (data.mode === 'AUTO') {
                        cardProg.classList.remove('hidden');
                    } else {
                        cardProg.classList.add('hidden');
                    }

                    let statusText = 'Inactive';
                    let stepNameText = '--';
                    if (data.sequence_active) {
                        if (data.waiting_for_delay) {
                            statusText = 'Waiting for Delayed Start (' + data.delayed_start_time + ')';
                            stepNameText = 'Waiting...';
                        } else {
                            statusText = 'Step ' + (data.current_step + 1);
                            if (data.current_step < data.steps.length) {
                                const sObj = data.steps[data.current_step];
                                stepNameText = (data.current_step + 1) + ' - ' + sObj.name + ' (' + sObj.temp + '°F)';
                            }
                        }
                    }
                    document.getElementById('seq-status').innerText = statusText;
                    document.getElementById('seq-step-info').innerText = stepNameText;

                    if (data.steps) {
                        data.steps.forEach((s, i) => {
                            const el = document.getElementById('step-spinner-' + i);
                            if (el) {
                                const isActive = (data.sequence_active && !data.waiting_for_delay && data.current_step === i);
                                el.innerHTML = isActive ? '<span class="spinner"></span>' : '';
                            }
                        });
                    }

                    const btnS = document.getElementById('btn-seq');
                    btnS.innerText = data.sequence_active ? 'STOP MASH PROFILE' : 'START MASH PROFILE';
                    btnS.className = data.sequence_active ? 'btn btn-stop' : 'btn btn-start';

                    const remaining = data.step_time_remaining;
                    const total = data.step_total_time;
                    const elapsed = Math.max(0, total - remaining);

                    document.getElementById('seq-elapsed').innerText = '[' + formatTime(elapsed) + ' / ' + formatTime(total) + ']';
                    document.getElementById('seq-timer').innerText = formatTime(remaining);

                    document.getElementById('lcd-temp-actual').innerText = Math.round(data.temp_actual);
                    document.getElementById('lcd-temp-target').innerText = Math.round(data.temp_objetivo);
                    document.getElementById('lcd-mode').innerText = data.mode;
                    document.getElementById('lcd-step').innerText = data.sequence_active ? ('S' + (data.current_step + 1)) : 'MAN';
                    document.getElementById('lcd-timer').innerText = formatTime(remaining).substring(3);
                    document.getElementById('lcd-state').innerText = data.sequence_active ? '▶' : '⏸';

                    document.getElementById('chk-delay').checked = data.delayed_start_enabled;
                    document.getElementById('time-delay').value = data.delayed_start_time;
                });
        }

        function toggleView() {
            const normal = document.getElementById('view-normal');
            const classic = document.getElementById('view-classic');
            const btnV = document.getElementById('btn-view');
            if (currentView === 'ADVANCED') {
                currentView = 'CLASSIC';
                normal.classList.add('hidden');
                classic.classList.remove('hidden');
                btnV.innerText = 'SWITCH TO ADVANCED VIEW';
            } else {
                currentView = 'ADVANCED';
                classic.classList.add('hidden');
                normal.classList.remove('hidden');
                btnV.innerText = 'SWITCH TO CLASSIC VIEW';
            }
        }

        function shutdownPi() {
            if (confirm("Are you sure you want to shut down the Raspberry Pi?")) {
                document.body.innerHTML = `
                    <div style="margin-top: 20vh; font-family: system-ui, sans-serif; color: #ff5252;">
                        <h2>🔴 Raspberry Pi is shutting down...</h2>
                        <p style="color: #ccc; font-size: 1.1rem; margin-top: 15px;">
                            Please wait ~15 seconds before disconnecting power safely.
                        </p>
                    </div>`;
                fetch('/api/shutdown', {method: 'POST'});
            }
        }

        function toggleDelay(enabled) {
            fetch('/api/delay/toggle', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            });
        }

        function updateDelayTime(timeStr) {
            fetch('/api/delay/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: timeStr})
            });
        }

        function renderSteps() {
            fetch('/api/status').then(res => res.json()).then(data => {
                let html = '';
                data.steps.forEach((s, i) => {
                    const isActive = (data.sequence_active && !data.waiting_for_delay && data.current_step === i);
                    html += `<tr>
                        <td><b>${i+1}</b></td>
                        <td style="white-space: nowrap;">
                            <input type="checkbox" ${s.enabled ? 'checked' : ''} onchange="updateStep(${i}, 'enabled', this.checked)">
                            <button onclick="jumpToStep(${i})" title="Run Step ${i+1}" style="padding: 3px 8px; background: #0288d1; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75rem; font-weight: bold; margin-left: 5px;">▶</button>
                        </td>
                        <td><span id="step-spinner-${i}">${isActive ? '<span class="spinner"></span>' : ''}</span></td>
                        <td><input type="number" value="${s.temp}" style="width: 50px;" onchange="updateStep(${i}, 'temp', parseFloat(this.value))"></td>
                        <td><input type="number" value="${s.hours}" style="width: 40px;" min="0" max="24" onchange="updateStep(${i}, 'hours', parseInt(this.value))"></td>
                        <td><input type="number" value="${s.mins}" style="width: 40px;" min="0" max="59" onchange="updateStep(${i}, 'mins', parseInt(this.value))"></td>
                    </tr>`;
                });
                document.getElementById('steps-table').innerHTML = html;
            });
        }

        function updateStep(idx, key, val) {
            fetch('/api/step/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: idx, key: key, value: val})
            });
        }

        function jumpToStep(idx) {
            fetch('/api/sequence/jump', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: idx})
            });
        }

        function toggleMode() {
            fetch('/api/mode/toggle', {method: 'POST'});
        }

        function toggleBoil() {
            fetch('/api/boil/toggle', {method: 'POST'});
        }

        function toggleSequence() {
            fetch('/api/sequence/toggle', {method: 'POST'});
        }

        function toggleCmd(target) {
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'TOGGLE', target: target})
            });
        }

        function setTarget(defaultVal, spinnerId) {
            let val = defaultVal;
            if (defaultVal === 163 && document.getElementById('target-strike')) {
                val = parseFloat(document.getElementById('target-strike').value);
            } else if (defaultVal === 152 && document.getElementById('target-mash')) {
                val = parseFloat(document.getElementById('target-mash').value);
            } else if (defaultVal === 170 && document.getElementById('target-mashout')) {
                val = parseFloat(document.getElementById('target-mashout').value);
            }

            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'SET_TEMP', value: val})
            });
        }

        function adjustTemp(amount) {
            fetch('/api/status').then(res => res.json()).then(data => {
                let newTarget = data.temp_objetivo + amount;
                fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'SET_TEMP', value: newTarget})
                });
            });
        }

        setInterval(updateStatus, 1000);
        updateStatus();
        renderSteps();
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

@app.route('/api/delay/toggle', methods=['POST'])
def delay_toggle():
    data = request.get_json() or {}
    state["delayed_start_enabled"] = data.get("enabled", False)
    return jsonify({"success": True, "delayed_start_enabled": state["delayed_start_enabled"]})

@app.route('/api/delay/update', methods=['POST'])
def delay_update():
    data = request.get_json() or {}
    state["delayed_start_time"] = data.get("time", "06:00")
    return jsonify({"success": True, "delayed_start_time": state["delayed_start_time"]})

@app.route('/api/step/update', methods=['POST'])
def update_step():
    data = request.get_json() or {}
    idx = data.get('index')
    key = data.get('key')
    val = data.get('value')
    if idx is not None and 0 <= idx < len(state["steps"]):
        state["steps"][idx][key] = val
    return jsonify({"success": True, "steps": state["steps"]})

@app.route('/api/mode/toggle', methods=['POST'])
def toggle_mode():
    state["mode"] = "AUTO" if state["mode"] == "MANUAL" else "MANUAL"
    return jsonify({"success": True, "mode": state["mode"]})

@app.route('/api/boil/toggle', methods=['POST'])
def toggle_boil():
    global ser, state
    state["boil_mode"] = not state["boil_mode"]
    if state["boil_mode"]:
        state["heater"] = True
        state["temp_objetivo"] = 212.0
        cmd = "SET:212.0\nH:H\n"
    else:
        state["heater"] = False
        cmd = "H:0\n"

    if ser and ser.is_open:
        try:
            ser.write(cmd.encode('utf-8'))
        except Exception as e:
            pass
            
    return jsonify({"success": True, "boil_mode": state["boil_mode"], "heater": state["heater"]})

@app.route('/api/sequence/toggle', methods=['POST'])
def toggle_sequence():
    global ser, state
    state["sequence_active"] = not state["sequence_active"]
    if state["sequence_active"]:
        state["current_step"] = 0
        state["waiting_for_delay"] = state["delayed_start_enabled"]
        first_step = state["steps"][0]
        state["step_total_time"] = (first_step["hours"] * 3600) + (first_step["mins"] * 60)
        state["step_time_remaining"] = state["step_total_time"]
        
        # Si NO hay delay, encendemos el calentador de inmediato
        if not state["waiting_for_delay"]:
            state["heater"] = True
            if ser and ser.is_open:
                try:
                    ser.write(b"H:1\n")
                except Exception:
                    pass
    else:
        state["waiting_for_delay"] = False
    return jsonify({"success": True, "sequence_active": state["sequence_active"]})

@app.route('/api/sequence/jump', methods=['POST'])
def jump_step():
    global ser, state
    data = request.get_json() or {}
    idx = data.get('index', 0)
    if 0 <= idx < len(state["steps"]):
        state["sequence_active"] = True
        state["waiting_for_delay"] = False
        state["steps"][idx]["enabled"] = True
        state["current_step"] = idx
        step = state["steps"][idx]
        state["step_total_time"] = (step["hours"] * 3600) + (step["mins"] * 60)
        state["step_time_remaining"] = state["step_total_time"]
        state["temp_objetivo"] = step["temp"]
        state["heater"] = True
        if ser and ser.is_open:
            try:
                ser.write(f"SET:{step['temp']}\nH:1\n".encode('utf-8'))
            except Exception:
                pass
    return jsonify({"success": True, "state": state})

@app.route('/api/shutdown', methods=['POST'])
def shutdown_pi():
    global ser, state
    state["heater"] = False
    state["boil_mode"] = False
    if ser and ser.is_open:
        try:
            ser.write(b"H:0\n")
        except Exception:
            pass

    def do_shutdown():
        time.sleep(1)
        os.system("sudo shutdown -h now")

    threading.Thread(target=do_shutdown, daemon=True).start()
    return jsonify({"success": True, "message": "Shutting down Raspberry Pi..."})

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
    elif action == "SET_TEMP":
        val = data.get("value", 163.0)
        state["temp_objetivo"] = val
        state["sequence_active"] = False
        state["waiting_for_delay"] = False
        cmd = f"SET:{val}\n"

    if ser and ser.is_open and cmd:
        try:
            ser.write(cmd.encode('utf-8'))
        except Exception as e:
            pass

    return jsonify({"success": True, "state": state})

t1 = threading.Thread(target=serial_loop, daemon=True)
t1.start()
t2 = threading.Thread(target=sequence_loop, daemon=True)
t2.start()

if __name__ == '__main__':
    cert_path = '/home/pi/BrewZilla/certs/brewzilla.local+3.pem'
    key_path = '/home/pi/BrewZilla/certs/brewzilla.local+3-key.pem'
    app.run(host='0.0.0.0', port=443, ssl_context=(cert_path, key_path), threaded=True, debug=False)
