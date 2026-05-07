"""
web_ui.py — HTML web interface for ReplitTermux.
Black/orange theme, live polling, SVG icons, animations.
"""
from history import CommandRecord


def render_web_ui(token: str, history: list) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReplitTermux</title>
<style>
  :root {{
    --bg:      #0a0a0a;
    --bg2:     #111111;
    --bg3:     #191919;
    --border:  #252525;
    --orange:  #ff6600;
    --orange2: #cc5200;
    --orange3: #ff8833;
    --text:    #e8e8e8;
    --muted:   #666;
    --green:   #22c55e;
    --red:     #ef4444;
    --radius:  10px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0;
       -webkit-tap-highlight-color: transparent; outline: none !important; }}
  ::selection {{ background: var(--orange); color: #000; }}
  html, body {{ height: 100%; }}
  body {{ background: var(--bg); color: var(--text);
          font-family: 'Segoe UI', system-ui, sans-serif;
          font-size: 15px; line-height: 1.5; }}

  /* ── Header ── */
  .header {{
    display: flex; align-items: center; gap: 12px;
    padding: 16px 20px;
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
  }}
  .header svg {{ flex-shrink: 0; }}
  .header-text h1 {{ color: var(--orange); font-size: 18px; font-weight: 700; letter-spacing: .3px; }}
  .header-text p  {{ color: var(--muted); font-size: 12px; }}
  .status-dot {{
    margin-left: auto; width: 10px; height: 10px; border-radius: 50%;
    background: var(--green); box-shadow: 0 0 8px var(--green);
    animation: pulse-dot 2s infinite;
  }}
  .status-dot.dead {{ background: var(--red); box-shadow: 0 0 8px var(--red); animation: none; }}
  @keyframes pulse-dot {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.4; }} }}

  /* ── Main layout ── */
  .main {{ padding: 16px 20px; max-width: 900px; margin: 0 auto; }}

  /* ── Command input ── */
  .cmd-wrap {{
    display: flex; gap: 10px; margin-bottom: 16px;
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 12px;
    transition: border-color .2s;
  }}
  .cmd-wrap:focus-within {{ border-color: var(--orange); }}
  .cmd-wrap svg {{ flex-shrink:0; align-self:center; opacity:.5; }}
  #ci {{
    flex: 1; background: transparent; color: var(--text);
    border: none; font-family: 'Courier New', monospace;
    font-size: 14px; min-width: 0;
  }}
  #ci::placeholder {{ color: var(--muted); }}
  #ci:focus {{ outline: none; }}
  #run-btn {{
    display: flex; align-items: center; gap: 6px;
    background: var(--orange); color: #000;
    border: none; border-radius: 7px;
    padding: 8px 16px; font-size: 13px; font-weight: 700;
    cursor: pointer; white-space: nowrap;
    transition: background .15s, transform .1s;
    flex-shrink: 0;
  }}
  #run-btn:hover  {{ background: var(--orange3); }}
  #run-btn:active {{ transform: scale(.96); }}
  #run-btn.loading {{ opacity: .6; pointer-events: none; }}

  /* ── Output pane ── */
  #out-wrap {{
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); margin-bottom: 16px;
    overflow: hidden; transition: max-height .3s;
  }}
  .out-header {{
    display: flex; align-items: center; gap: 8px;
    padding: 8px 14px; border-bottom: 1px solid var(--border);
    font-size: 12px; color: var(--muted);
  }}
  .exit-ok  {{ color: var(--green); font-weight: 700; }}
  .exit-err {{ color: var(--red);   font-weight: 700; }}
  #out {{
    padding: 12px 14px;
    font-family: 'Courier New', monospace;
    font-size: 13px; line-height: 1.6;
    white-space: pre-wrap; word-break: break-all;
    max-height: 240px; overflow-y: auto;
    color: #ccc;
  }}

  /* ── History table ── */
  .section-title {{
    display: flex; align-items: center; gap: 8px;
    color: var(--muted); font-size: 12px; text-transform: uppercase;
    letter-spacing: .8px; margin-bottom: 10px;
  }}
  .section-title span {{ flex:1; height:1px; background:var(--border); }}

  .history-list {{ display: flex; flex-direction: column; gap: 6px; }}
  .h-row {{
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 14px;
    cursor: pointer; transition: border-color .15s, background .15s;
    animation: row-in .25s ease;
  }}
  .h-row:hover {{ border-color: var(--orange2); background: var(--bg3); }}
  @keyframes row-in {{
    from {{ opacity:0; transform:translateY(-6px); }}
    to   {{ opacity:1; transform:translateY(0); }}
  }}
  .h-row-top {{
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  }}
  .h-icon {{ flex-shrink:0; width:18px; height:18px; }}
  .h-cmd {{
    flex: 1; font-family: 'Courier New', monospace;
    font-size: 13px; font-weight: 600; color: var(--text);
    word-break: break-all; min-width: 0;
  }}
  .h-meta {{
    display: flex; align-items: center; gap: 8px;
    flex-shrink: 0; font-size: 11px; color: var(--muted);
  }}
  .h-code-ok  {{ color: var(--green); }}
  .h-code-err {{ color: var(--red); }}
  .h-out {{
    display: none; margin-top: 8px; padding: 8px 10px;
    background: var(--bg); border-radius: 6px;
    font-family: 'Courier New', monospace; font-size: 12px;
    color: #aaa; white-space: pre-wrap; word-break: break-all;
    max-height: 180px; overflow-y: auto;
    border: 1px solid var(--border);
  }}
  .h-row.open .h-out {{ display: block; }}

  /* ── Empty state ── */
  .empty {{
    text-align: center; padding: 40px 20px;
    color: var(--muted); font-size: 14px;
  }}
  .empty svg {{ margin: 0 auto 12px; display:block; opacity:.3; }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--orange2); }}

  @media(max-width: 480px) {{
    .main {{ padding: 12px; }}
    .header {{ padding: 12px; }}
    #run-btn {{ padding: 8px 12px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
    <rect width="24" height="24" rx="6" fill="#ff6600" fill-opacity=".15"/>
    <path d="M4 7h16M4 12h10M4 17h7" stroke="#ff6600" stroke-width="2" stroke-linecap="round"/>
    <path d="M15 15l3 3-3 3" stroke="#ff6600" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  <div class="header-text">
    <h1>ReplitTermux</h1>
    <p>Bridge — команды выполняются в Termux в реальном времени</p>
  </div>
  <div class="status-dot" id="dot" title="Соединение активно"></div>
</div>

<div class="main">

  <!-- Command input -->
  <div class="cmd-wrap">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <path d="M4 17l6-6-6-6M11 19h9" stroke="#ff6600" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <input id="ci" placeholder="ls / pwd / uname -a / cat /etc/os-release ..."
           autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false">
    <button id="run-btn" onclick="go()">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
        <path d="M5 3l14 9-14 9V3z"/>
      </svg>
      Run
    </button>
  </div>

  <!-- Output pane -->
  <div id="out-wrap">
    <div class="out-header">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="18" height="18" rx="3" stroke="#666" stroke-width="2"/>
        <path d="M7 9l4 4-4 4M13 17h4" stroke="#666" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span id="out-label">Вывод появится здесь</span>
      <span id="out-exit" style="margin-left:auto"></span>
    </div>
    <pre id="out"> </pre>
  </div>

  <!-- History -->
  <div class="section-title">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="#666" stroke-width="2"/>
      <path d="M12 7v5l3 3" stroke="#666" stroke-width="2" stroke-linecap="round"/>
    </svg>
    История команд
    <span></span>
    <span id="hist-count" style="color:var(--orange);font-size:11px"></span>
  </div>
  <div class="history-list" id="hist"></div>

</div>

<script>
const TOKEN = "{token}";
const BASE  = window.location.origin;
let _lastTs = null;
let _known  = {{}};

function esc(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}
function fmtOut(s) {{
  return esc(s.slice(0, 2000)) + (s.length > 2000 ? '\\n…' : '');
}}

async function go() {{
  const cmd = document.getElementById('ci').value.trim();
  if (!cmd) return;
  const btn = document.getElementById('run-btn');
  const out = document.getElementById('out');
  const label = document.getElementById('out-label');
  const exitEl = document.getElementById('out-exit');
  btn.classList.add('loading');
  btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" stroke-dasharray="28" stroke-dashoffset="10" style="animation:spin .8s linear infinite;transform-origin:center"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur=".8s" repeatCount="indefinite"/></circle></svg> ...';
  label.textContent = '⏳ ' + cmd;
  exitEl.textContent = '';
  out.textContent = '';
  try {{
    const r = await fetch(BASE + '/run', {{
      method: 'POST',
      headers: {{ 'Content-Type':'application/json', 'X-Token': TOKEN }},
      body: JSON.stringify({{ cmd }})
    }});
    const d = await r.json();
    out.textContent = d.out || '(нет вывода)';
    label.textContent = cmd;
    const ok = d.code === 0;
    exitEl.innerHTML = `<span class="${{ok ? 'exit-ok' : 'exit-err'}}">EXIT ${{d.code}}</span>&nbsp;<span style="color:var(--muted)">${{d.elapsed}}s</span>`;
    document.getElementById('ci').value = '';
  }} catch(e) {{
    out.textContent = 'Ошибка: ' + e;
    label.textContent = 'Ошибка';
  }}
  btn.classList.remove('loading');
  btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M5 3l14 9-14 9V3z"/></svg> Run';
  await loadHistory();
}}

document.getElementById('ci').addEventListener('keydown', e => {{
  if (e.key === 'Enter') go();
}});

function makeRow(h) {{
  const ok  = h.code === 0;
  const out = fmtOut(h.out || '');
  const iconSvg = ok
    ? `<svg class="h-icon" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="#22c55e22"/><path d="M7 12l4 4 6-7" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    : `<svg class="h-icon" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="#ef444422"/><path d="M8 8l8 8M16 8l-8 8" stroke="#ef4444" stroke-width="2" stroke-linecap="round"/></svg>`;
  return `
    <div class="h-row" onclick="this.classList.toggle('open')">
      <div class="h-row-top">
        ${{iconSvg}}
        <span class="h-cmd">${{esc(h.cmd)}}</span>
        <span class="h-meta">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="#666" stroke-width="2"/>
            <path d="M12 7v5l3 3" stroke="#666" stroke-width="2" stroke-linecap="round"/>
          </svg>
          ${{esc(h.ts)}}
          &nbsp;<span class="${{ok ? 'h-code-ok' : 'h-code-err'}}">${{h.code}}</span>
          &nbsp;<span style="color:var(--muted)">${{h.elapsed}}s</span>
        </span>
      </div>
      ${{out ? `<div class="h-out">${{out}}</div>` : ''}}
    </div>`;
}}

async function loadHistory() {{
  try {{
    const r = await fetch(BASE + '/history?n=100', {{ headers: {{ 'X-Token': TOKEN }} }});
    if (!r.ok) {{ setDead(); return; }}
    const data = await r.json();
    setAlive();
    const list = document.getElementById('hist');
    const count = document.getElementById('hist-count');
    if (!data.length) {{
      list.innerHTML = `<div class="empty">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
          <path d="M4 7h16M4 12h10M4 17h7" stroke="#444" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Нет команд в истории
      </div>`;
      count.textContent = '';
      return;
    }}
    count.textContent = data.length;
    // Добавляем только новые записи (по ts+cmd ключу)
    const newItems = data.filter(h => {{
      const key = h.ts + '|' + h.cmd;
      if (_known[key]) return false;
      _known[key] = true;
      return true;
    }});
    if (newItems.length) {{
      // Перерисовываем полностью (проще и надёжнее при малом объёме)
      list.innerHTML = data.slice().reverse().map(makeRow).join('');
    }}
  }} catch(e) {{ setDead(); }}
}}

function setAlive() {{
  document.getElementById('dot').className = 'status-dot';
}}
function setDead() {{
  document.getElementById('dot').className = 'status-dot dead';
}}

// Polling
loadHistory();
setInterval(loadHistory, 2000);
</script>
</body>
</html>"""
