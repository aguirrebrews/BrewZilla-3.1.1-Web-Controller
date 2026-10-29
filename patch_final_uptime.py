import re

# 1. Asegurar respuesta en web_brewzilla.py
web_path = "/home/pi/BrewZilla/web_brewzilla.py"
with open(web_path, "r", encoding="utf-8") as f:
    code = f.read()

if "def get_uptimes():" not in code:
    uptime_backend = '''
def get_uptimes():
    try:
        with open('/proc/uptime', 'r') as f:
            sys_sec = float(f.readline().split()[0])
            sys_str = f"{int(sys_sec // 3600)}h {int((sys_sec % 3600) // 60)}m"
    except Exception:
        sys_str = "N/A"

    svc_sec = (datetime.now() - SERVICE_START_TIME).total_seconds()
    svc_str = f"{int(svc_sec // 3600)}h {int((svc_sec % 3600) // 60)}m"
    start_str = SERVICE_START_TIME.strftime("%m/%d/%Y - %I:%M %p")
    return sys_str, svc_str, start_str
'''
    code = "from datetime import datetime\nSERVICE_START_TIME = datetime.now()\n" + code + uptime_backend

if 'state["sys_uptime"]' not in code:
    code = re.sub(
        r'(return jsonify\((?:state|data)\))',
        r'sys_u, svc_u, st = get_uptimes()\n    state["sys_uptime"] = sys_u\n    state["svc_uptime"] = svc_u\n    state["service_start"] = st\n    \1',
        code
    )

with open(web_path, "w", encoding="utf-8") as f:
    f.write(code)

# 2. Asegurar JS en templates/index.html
html_path = "/home/pi/BrewZilla/templates/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

js_injector = '''
                    if (data.sys_uptime) {
                        const elSys = document.getElementById("sys-uptime");
                        const elSvc = document.getElementById("svc-uptime");
                        const elSt = document.getElementById("svc-start");
                        if (elSys) elSys.innerText = data.sys_uptime;
                        if (elSvc) elSvc.innerText = data.svc_uptime;
                        if (elSt) elSt.innerText = data.service_start;
                    }
'''

if 'document.getElementById("sys-uptime")' not in html or 'data.sys_uptime' not in html:
    html = re.sub(r'(\.then\(data\s*=>\s*\{)', r'\1' + js_injector, html, count=1)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Actualización de Uptime completada.")
