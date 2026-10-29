import re

file_path = "/home/pi/BrewZilla/web_brewzilla.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Asegurar import de datetime y SERVICE_START_TIME
if "SERVICE_START_TIME" not in code:
    code = "from datetime import datetime\nSERVICE_START_TIME = datetime.now()\n" + code

# 2. Agregar función helper de Uptimes si no existe
if "def get_uptimes():" not in code:
    uptime_helper = '''
def get_uptimes():
    try:
        with open('/proc/uptime', 'r') as f:
            sys_seconds = float(f.readline().split()[0])
            sys_hours = int(sys_seconds // 3600)
            sys_mins = int((sys_seconds % 3600) // 60)
            sys_str = f"{sys_hours}h {sys_mins}m"
    except Exception:
        sys_str = "N/A"

    svc_seconds = (datetime.now() - SERVICE_START_TIME).total_seconds()
    svc_hours = int(svc_seconds // 3600)
    svc_mins = int((svc_seconds % 3600) // 60)
    svc_str = f"{svc_hours}h {svc_mins}m"
    start_str = SERVICE_START_TIME.strftime("%m/%d/%Y - %I:%M %p")
    return sys_str, svc_str, start_str
'''
    code += uptime_helper

# 3. Inyectar datos de uptime en la respuesta de /api/status y /api/state
if 'state["sys_uptime"]' not in code:
    code = re.sub(
        r'(def get_status\(\):.*?\n\s*)(return jsonify\(state\))',
        r'\1sys_u, svc_u, st = get_uptimes()\n    state["sys_uptime"] = sys_u\n    state["svc_uptime"] = svc_u\n    state["service_start"] = st\n    \2',
        code,
        flags=re.DOTALL
    )

# 4. Inyectar el HTML del footer al final del HTML_TEMPLATE
footer_html = '<div id="uptime-footer" style="text-align: center; font-size: 0.75rem; color: #888888; margin-top: 25px; margin-bottom: 15px; font-family: monospace;">Pi Uptime: <span id="sys-uptime">--</span> | Web Uptime: <span id="svc-uptime">--</span> (Since: <span id="svc-start">--</span>)</div>'

if 'id="uptime-footer"' not in code:
    code = code.replace('</body>', f'{footer_html}\\n</body>')

# 5. Inyectar la actualización de JS dentro del fetch de updateStatus()
js_update = '''
                    if (data.sys_uptime) document.getElementById("sys-uptime").innerText = data.sys_uptime;
                    if (data.svc_uptime) document.getElementById("svc-uptime").innerText = data.svc_uptime;
                    if (data.service_start) document.getElementById("svc-start").innerText = data.service_start;
'''

if 'document.getElementById("sys-uptime")' not in code:
    code = re.sub(r'(\.then\(data\s*=>\s*\{)', r'\1' + js_update, code, count=1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Inyección directa en GOLDEN completada con éxito.")
