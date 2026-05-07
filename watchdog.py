"""
  watchdog.py — ReplitTermux self-management daemon.

  Runs in a separate tmux session (rt-watch). Never dies with the bridge.
  Responsibilities:
    - Auto-restart the bridge if it goes down
    - Handle control signals from control.txt or /ctrl endpoint
    - Write current bridge URL to bridge_url.txt after each (re)start
    - Send Telegram notification with new URL on every restart

  Control signals (write to bridge_url.txt/../control.txt or POST /ctrl):
    RESTART  — kill bridge, restart with current code
    UPDATE   — git pull, then restart
    STOP     — kill bridge, exit watchdog
  """
  import os, sys, time, json, signal, subprocess, urllib.request
  from pathlib import Path
  from datetime import datetime

  BRIDGE_DIR   = Path(__file__).parent.resolve()
  BRIDGE_PORT  = int(os.environ.get("RT_PORT", 7474))
  CTRL_FILE    = BRIDGE_DIR / "control.txt"
  URL_FILE     = BRIDGE_DIR / "bridge_url.txt"
  PID_FILE     = BRIDGE_DIR / "bridge.pid"
  LOG_FILE     = BRIDGE_DIR / "watchdog.log"
  CHECK_EVERY  = 12   # seconds between health checks
  URL_WAIT     = 60   # seconds to wait for URL after bridge start


  def log(msg: str) -> None:
      line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
      print(line, flush=True)
      try:
          with open(LOG_FILE, "a", encoding="utf-8") as f:
              f.write(line + "\n")
      except Exception:
          pass


  def is_bridge_alive() -> bool:
      try:
          import urllib.request
          r = urllib.request.urlopen(
              f"http://127.0.0.1:{BRIDGE_PORT}/ping", timeout=4
          )
          return r.status == 200
      except Exception:
          return False


  def kill_bridge() -> None:
      # Kill by PID file first
      if PID_FILE.exists():
          try:
              pid = int(PID_FILE.read_text().strip())
              os.kill(pid, signal.SIGTERM)
              time.sleep(1)
              try:
                  os.kill(pid, signal.SIGKILL)
              except ProcessLookupError:
                  pass
          except Exception:
              pass
          PID_FILE.unlink(missing_ok=True)
      # Also sweep any stray most.py processes
      subprocess.run(
          "pkill -f 'python.*most.py' 2>/dev/null; pkill -f 'python3.*most.py' 2>/dev/null",
          shell=True,
      )
      time.sleep(1)


  def git_pull() -> None:
      log("Running git pull...")
      r = subprocess.run(
          "git pull", shell=True, cwd=BRIDGE_DIR,
          capture_output=True,
      )
      out = (r.stdout + r.stderr).decode("utf-8", errors="replace").strip()
      log(f"git pull result: {out[:300]}")


  def start_bridge() -> subprocess.Popen:
      URL_FILE.unlink(missing_ok=True)
      log("Starting bridge (RT_NONINTERACTIVE=1)...")
      env = {**os.environ, "RT_NONINTERACTIVE": "1", "PYTHONIOENCODING": "utf-8"}
      proc = subprocess.Popen(
          [sys.executable, str(BRIDGE_DIR / "most.py")],
          cwd=BRIDGE_DIR,
          env=env,
          stdout=open(BRIDGE_DIR / "bridge.log", "w", encoding="utf-8"),
          stderr=subprocess.STDOUT,
      )
      PID_FILE.write_text(str(proc.pid))
      log(f"Bridge PID={proc.pid}")
      return proc


  def wait_for_url(timeout: int = URL_WAIT) -> str:
      """Block until bridge_url.txt appears or timeout."""
      deadline = time.time() + timeout
      while time.time() < deadline:
          if URL_FILE.exists():
              url = URL_FILE.read_text(encoding="utf-8").strip()
              if url.startswith("http"):
                  return url
          time.sleep(2)
      return ""


  def notify_telegram(text: str) -> None:
      try:
          conf = Path.home() / ".replittermux.conf"
          if not conf.exists():
              return
          cfg = json.loads(conf.read_text(encoding="utf-8"))
          bot_token = cfg.get("bot_token", "")
          chat_id   = cfg.get("chat_id", "")
          if not bot_token or not chat_id:
              return
          payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
          req = urllib.request.Request(
              f"https://api.telegram.org/bot{bot_token}/sendMessage",
              data=payload,
              headers={"Content-Type": "application/json"},
          )
          urllib.request.urlopen(req, timeout=10)
          log("Telegram notified.")
      except Exception as e:
          log(f"Telegram notify failed: {e}")


  def read_ctrl() -> str:
      """Read and clear control.txt. Returns '' if no signal."""
      if CTRL_FILE.exists():
          try:
              cmd = CTRL_FILE.read_text(encoding="utf-8").strip().upper()
              CTRL_FILE.unlink(missing_ok=True)
              return cmd
          except Exception:
              pass
      return ""


  def restart_cycle(do_pull: bool = False) -> None:
      kill_bridge()
      if do_pull:
          git_pull()
      start_bridge()
      url = wait_for_url()
      if url:
          log(f"Bridge online: {url}")
          notify_telegram(
              f"ReplitTermux restarted\n"
              f"URL: {url}\n"
              f"{'(git pull applied)' if do_pull else ''}"
          )
      else:
          log("WARNING: bridge started but URL not detected within timeout")


  def main() -> None:
      log("=== Watchdog started ===")

      if not is_bridge_alive():
          log("Bridge not running — starting fresh")
          restart_cycle()
      else:
          log("Bridge already alive — watchdog in standby")

      while True:
          time.sleep(CHECK_EVERY)

          ctrl = read_ctrl()
          if ctrl == "STOP":
              log("STOP signal — killing bridge and exiting")
              kill_bridge()
              break
          elif ctrl == "UPDATE":
              log("UPDATE signal — git pull + restart")
              restart_cycle(do_pull=True)
              continue
          elif ctrl == "RESTART":
              log("RESTART signal — restarting bridge")
              restart_cycle()
              continue

          if not is_bridge_alive():
              log("Bridge dead — auto-restart")
              restart_cycle()


  if __name__ == "__main__":
      main()
  