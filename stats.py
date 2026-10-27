import urllib.request
import json
import time
import os
import ssl

# Ignorar verificación SSL para el certificado local
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req_count = 0
err_count = 0
start_time = time.time()

try:
    while True:
        t_start = time.time()
        try:
            req = urllib.request.urlopen('https://localhost/api/status', context=ctx, timeout=2)
            latency = (time.time() - t_start) * 1000
            data = json.loads(req.read().decode('utf-8'))
            req_count += 1
            
            uptime = int(time.time() - start_time)
            conn_str = f"ONLINE ({data.get('last_update', 'N/A')})" if data.get('connected') else "DISCONNECTED"
            heater_str = "BOIL (H:H)" if data.get('boil_mode') else ("ON (H:1)" if data.get('heater') else "OFF (H:0)")
            pump_str = "ON (P:1)" if data.get('pump') else "OFF (P:0)"

            os.system('clear')
            print("\033[92m┌──────────────────────────────────────────────────────────┐\033[0m")
            print("\033[92m│               🤓 BREWZILLA STATS FOR NERDS               │\033[0m")
            print("\033[92m├──────────────────────────────────────────────────────────┤\033[0m")
            print(f"│ Target Endpoint   : https://localhost/api/status          │")
            print(f"│ Serial Interface  : /dev/ARDUINO -> /dev/ttyUSB0          │")
            print(f"│ Serial Link       : {conn_str:<36} │")
            print(f"│ Latency (Ping)    : {latency:>6.2f} ms                           │")
            print(f"│ Monitor Uptime    : {uptime:>6} s                            │")
            print(f"│ Total Polls (RX)  : {req_count:<36} │")
            print(f"│ Poll Errors       : {err_count:<36} │")
            print("\033[92m├──────────────────────────────────────────────────────────┤\033[0m")
            print(f"│ Current Temp (T)  : {data.get('temp_actual', 0.0):>6.1f} °F                          │")
            print(f"│ Target Temp (SET) : {data.get('temp_objetivo', 0.0):>6.1f} °F                          │")
            print(f"│ Heater State (H)  : {heater_str:<36} │")
            print(f"│ Pump State (P)    : {pump_str:<36} │")
            print(f"│ System Mode       : {data.get('mode', 'N/A'):<36} │")
            print("\033[92m└──────────────────────────────────────────────────────────┘\033[0m")
            print(" Presiona Ctrl+C para salir.")
        except Exception as e:
            err_count += 1
            os.system('clear')
            print(f"Conectando con el servidor Flask... (Reintentos: {err_count})")
        
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMonitor detenido.")
