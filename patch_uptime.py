import re
from datetime import datetime

file_path = "/home/pi/BrewZilla/web_brewzilla.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Agregar variables globales de tiempo de inicio del servicio si no existen
if "SERVICE_START_TIME" not in code:
    imports_patch = "import os\nimport time\nfrom datetime import datetime\nSERVICE_START_TIME = datetime.now()\n"
    code = re.sub(r"(import os\n|import time\n)", imports_patch, code, count=1)

# 2. Función helper para obtener el uptime del SO y del servicio
uptime_func = '''
def get_uptimes():
    # Uptime del sistema operativo (Raspberry Pi)
    try:
        with open('/proc/uptime', 'r') as f:
            sys_seconds = float(f.readline().split()[0])
            sys_days = int(sys_seconds // 86400)
            sys_hours = int((sys_seconds % 86400) // 3600)
            sys_mins = int((sys_seconds % 3600) // 60)
            sys_str = f"{sys_days}d {sys_hours}h {sys_mins}m" if sys_days > 0 else f"{sys_hours}h {sys_mins}m"
    except Exception:
        sys_str = "N/A"

    # Uptime del servicio de Python/Gunicorn
    svc_seconds = (datetime.now() - SERVICE_START_TIME).total_seconds()
    svc_days = int(svc_seconds // 86400)
    svc_hours = int((svc_seconds % 86400) // 3600)
    svc_mins = int((svc_seconds % 3600) // 60)
    svc_str = f"{svc_days}d {svc_hours}h {svc_mins}m" if svc_days > 0 else f"{svc_hours}h {svc_mins}m"

    start_date_str = SERVICE_START_TIME.strftime("%m/%d/%Y - %I:%M %p")
    return sys_str, svc_str, start_date_str
'''

if "def get_uptimes():" not in code:
    code += uptime_func

# 3. Incluir las claves de uptime dentro del estado global en cada ciclo de actualización
if '"sys_uptime"' not in code:
    code = re.sub(
        r'(state\["last_update"\]\s*=\s*datetime\.now\(\)\.strftime\("[^"]+"\)\s*)',
        r'\1    sys_up, svc_up, start_dt = get_uptimes()\n    state["sys_uptime"] = sys_up\n    state["svc_uptime"] = svc_up\n    state["service_start"] = start_dt\n',
        code
    )

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Backend actualizado con cálculo de Uptimes.")
