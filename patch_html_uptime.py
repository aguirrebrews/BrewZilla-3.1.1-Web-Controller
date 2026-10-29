import re

file_path = "/home/pi/BrewZilla/templates/index.html"

with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Insertar el contenedor HTML para el Uptime al final de la página
footer_html = '''
<div id="uptime-footer" style="text-align: center; font-size: 0.75rem; color: #888888; margin-top: 25px; margin-bottom: 15px; font-family: monospace;">
    Pi Uptime: <span id="sys-uptime">--</span> | Web Uptime: <span id="svc-uptime">--</span> (Since: <span id="svc-start">--</span>)
</div>
'''

if 'id="uptime-footer"' not in html:
    html = html.replace('</body>', f'{footer_html}\n</body>')

# 2. Actualizar los campos dinámicos en JavaScript
js_update = '''
    if (data.sys_uptime) document.getElementById("sys-uptime").innerText = data.sys_uptime;
    if (data.svc_uptime) document.getElementById("svc-uptime").innerText = data.svc_uptime;
    if (data.service_start) document.getElementById("svc-start").innerText = data.service_start;
'''

if 'document.getElementById("sys-uptime")' not in html:
    html = re.sub(r'(\}\s*catch\s*\(e\)\s*\{|\n\s*\}\s*</script>)', f'{js_update}\n\\1', html, count=1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Interfaz HTML/JS actualizada con el pie de página de Uptime.")
