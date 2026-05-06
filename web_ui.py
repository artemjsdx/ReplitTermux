"""
web_ui.py — HTML web interface template.
S: One responsibility — generate the browser-based control panel HTML.
"""
from .history import CommandRecord


def render_web_ui(token: str, history: list[CommandRecord]) -> str:
    rows = ""
    for h in reversed(history[-30:]):
        icon  = "✅" if h.code == 0 else "❌"
        out_s = h.out.replace("<", "&lt;").replace("\n", "<br>")[:500]
        rows += (
            f"<tr>"
            f"<td style='white-space:nowrap'>{h.ts}</td>"
            f"<td style='font-family:monospace;font-weight:bold'>{h.cmd[:60]}</td>"
            f"<td>{icon} {h.code}</td>"
            f"<td style='font-family:monospace;font-size:12px;color:#aaa'>{out_s}</td>"
            f"</tr>"
        )

    return f"""<!DOCTYPE html><html lang="ru">
<head><meta charset="UTF-8"><title>ReplitTermux</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;padding:24px}}
h1{{color:#ff8c00;font-size:22px;margin-bottom:4px}}
.sub{{color:#8b949e;font-size:13px;margin-bottom:20px}}
.cmd-box{{display:flex;gap:8px;margin-bottom:20px}}
input{{flex:1;background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:6px;
       padding:10px 14px;font-family:monospace;font-size:14px;outline:none}}
input:focus{{border-color:#ff8c00}}
button{{background:#ff8c00;color:#000;border:none;border-radius:6px;
        padding:10px 20px;font-weight:700;cursor:pointer}}
button:hover{{background:#e07c00}}
pre{{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:14px;
     font-size:13px;white-space:pre-wrap;word-break:break-all;margin-bottom:20px;
     min-height:48px;max-height:300px;overflow-y:auto}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:#8b949e;font-size:12px;border-bottom:1px solid #21262d;padding:8px 6px}}
td{{padding:7px 6px;border-bottom:1px solid #161b22;font-size:13px;vertical-align:top}}
</style></head>
<body>
<h1>🔗 ReplitTermux</h1>
<p class="sub">Bridge — команды выполняются в Termux в реальном времени</p>
<div class="cmd-box">
  <input id="ci" placeholder="ls / pwd / uname -a / cat /etc/os-release ..."
         onkeydown="if(event.key==='Enter')go()">
  <button onclick="go()">▶ Run</button>
</div>
<pre id="out">Вывод появится здесь...</pre>
<table>
  <tr><th>Время</th><th>Команда</th><th>Код</th><th>Вывод</th></tr>
  {rows}
</table>
<script>
const TOKEN = "{token}";
async function go() {{
  const cmd = document.getElementById('ci').value.trim();
  if (!cmd) return;
  const out = document.getElementById('out');
  out.textContent = '⏳ Выполняется...';
  try {{
    const r = await fetch('/run', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json','X-Token':TOKEN}},
      body: JSON.stringify({{cmd}})
    }});
    const d = await r.json();
    out.textContent = (d.out || '(нет вывода)') + `\\n\\nEXIT ${{d.code}}  (${{d.elapsed}}s)`;
    setTimeout(()=>location.reload(), 1500);
  }} catch(e) {{ out.textContent = 'Ошибка: '+e; }}
}}
</script>
</body></html>"""
