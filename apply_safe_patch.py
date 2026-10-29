import re

path = "/home/pi/BrewZilla/web_brewzilla.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Parche quirúrgico 1: Agregar try-except en la función send_command
old_set_logic = 'state["temp_objetivo"] = float(val)'
new_set_logic = '''try:
            state["temp_objetivo"] = float(val)
        except (ValueError, TypeError):
            pass'''

if old_set_logic in code:
    code = code.replace(old_set_logic, new_set_logic)

# Parche quirúrgico 2: Asegurar flag de conexion en loop serial
if 'state["connected"] = True' not in code:
    code = code.replace('state["last_update"] = time.strftime("%H:%M:%S")', 'state["last_update"] = time.strftime("%H:%M:%S")\n                state["connected"] = True')

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("PARCHE_SEGURO_APLICADO")
