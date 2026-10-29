import re

file_path = "/home/pi/BrewZilla/web_brewzilla.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Asegurar envio de PING en el loop serial
if 'ser.write(b"PING\\n")' not in code and "ser.write" in code:
    code = re.sub(r"(ser\.readline\(\))", r'ser.write(b"PING\\n")\n            \1', code)

# 2. Reemplazar la evaluacion string == por >= en delayed start
old_delay_check = r"now\.strftime\([^\)]+\)\s*==\s*state\[[\"']delayed_start_time[\"']\]"
new_delay_check = 'datetime.now() >= datetime.strptime(state["delayed_start_time"], "%H:%M").replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)'

if re.search(old_delay_check, code):
    code = re.sub(old_delay_check, new_delay_check, code)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Parche aplicado exitosamente a web_brewzilla.py")
