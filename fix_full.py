import re

path = "/home/pi/BrewZilla/web_brewzilla.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

correct_func = """@app.route('/api/command', methods=['POST'])
def send_command():
    global ser, state
    data = request.get_json() or {}
    cmd = ""
    action = data.get("action")
    if action == "SET_TEMP":
        val = data.get("value", 163.0)
        try:
            state["temp_objetivo"] = float(val)
            cmd = "T:" + str(round(state["temp_objetivo"], 1)) + "\\n"
        except Exception:
            pass
    elif action == "TOGGLE":
        target = data.get("target")
        if target == "HEATER":
            state["heater"] = not state["heater"]
            cmd = "H:1\\n" if state["heater"] else "H:0\\n"
        elif target == "PUMP":
            state["pump"] = not state["pump"]
            cmd = "P:1\\n" if state["pump"] else "P:0\\n"

    if ser and ser.is_open and cmd:
        try:
            ser.write(cmd.encode('utf-8'))
            ser.flush()
        except Exception as e:
            print("Error serial:", e)

    return jsonify({"success": True, "state": state})"""

pattern = r"@app\.route\('/api/command', methods=\['POST'\]\).*?(?=@app\.route|\Z)"
if re.search(pattern, code, re.DOTALL):
    code = re.sub(pattern, correct_func + "\n\n", code, flags=re.DOTALL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("CODIGO_CORREGIDO")
