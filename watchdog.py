import os, sys, time, json, signal, subprocess, urllib.request
from pathlib import Path
from datetime import datetime

BRIDGE_DIR   = Path(__file__).parent.resolve()
BRIDGE_PORT  = int(os.environ.get("RT_PORT", 7474))
CTRL_FILE    = BRIDGE_DIR / "control.txt"
URL_FILE     = BRIDGE_DIR / "bridge_url.txt"
PID_FILE     = BRIDGE_DIR / "bridge.pid"
LOG_FILE     = BRIDGE_DIR / "watchdog.log"
CHECK_EVERY  = 12
URL_WAIT     = 60


def log(msg):
    line = "[{}] {}".format(datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def is_bridge_alive():
    try:
        import urllib.request as ur
        r = ur.urlopen("http://127.0.0.1:{}/ping".format(BRIDGE_PORT), timeout=4)
        return r.status == 200
    except Exception:
        return False


def kill_bridge():
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
        try:
            PID_FILE.unlink()
        except Exception:
            pass
    subprocess.run(
        "pkill -f 'python.*most.py' 2>/dev/null; pkill -f 'python3.*most.py' 2>/dev/null",
        shell=True,
    )
    time.sleep(1)


def git_pull():
    log("Running git pull...")
    r = subprocess.run("git pull", shell=True, cwd=str(BRIDGE_DIR), capture_output=True)
    out = (r.stdout + r.stderr).decode("utf-8", errors="replace").strip()
    log("git pull: " + out[:300])


def start_bridge():
    try:
        URL_FILE.unlink()
    except Exception:
        pass
    log("Starting bridge (RT_NONINTERACTIVE=1)...")
    env = dict(os.environ)
    env["RT_NONINTERACTIVE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        [sys.executable, str(BRIDGE_DIR / "most.py")],
        cwd=str(BRIDGE_DIR),
        env=env,
        stdout=open(str(BRIDGE_DIR / "bridge.log"), "w", encoding="utf-8"),
        stderr=subprocess.STDOUT,
    )
    PID_FILE.write_text(str(proc.pid))
    log("Bridge PID={}".format(proc.pid))
    return proc


def wait_for_url():
    deadline = time.time() + URL_WAIT
    while time.time() < deadline:
        if URL_FILE.exists():
            try:
                url = URL_FILE.read_text(encoding="utf-8").strip()
                if url.startswith("http"):
                    return url
            except Exception:
                pass
        time.sleep(2)
    return ""


def notify_telegram(text):
    try:
        conf = Path.home() / ".replittermux.conf"
        if not conf.exists():
            return
        cfg = json.loads(conf.read_text(encoding="utf-8"))
        bot_token = cfg.get("bot_token", "")
        chat_id   = cfg.get("chat_id", "")
        if not bot_token or not chat_id:
            return
        import urllib.request as ur
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = ur.Request(
            "https://api.telegram.org/bot{}/sendMessage".format(bot_token),
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        ur.urlopen(req, timeout=10)
        log("Telegram notified.")
    except Exception as e:
        log("Telegram notify failed: {}".format(e))


def read_ctrl():
    if CTRL_FILE.exists():
        try:
            cmd = CTRL_FILE.read_text(encoding="utf-8").strip().upper()
            try:
                CTRL_FILE.unlink()
            except Exception:
                pass
            return cmd
        except Exception:
            pass
    return ""


def restart_cycle(do_pull=False):
    kill_bridge()
    if do_pull:
        git_pull()
    start_bridge()
    url = wait_for_url()
    if url:
        log("Bridge online: " + url)
        notify_telegram(
            "ReplitTermux restarted\nURL: {}\n{}".format(
                url, "(git pull applied)" if do_pull else ""
            )
        )
    else:
        log("WARNING: bridge started but URL not detected within timeout")


def main():
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
            log("STOP — killing bridge and exiting")
            kill_bridge()
            break
        elif ctrl == "UPDATE":
            log("UPDATE — git pull + restart")
            restart_cycle(do_pull=True)
        elif ctrl == "RESTART":
            log("RESTART — restarting bridge")
            restart_cycle()
        elif not is_bridge_alive():
            log("Bridge dead — auto-restart")
            restart_cycle()


if __name__ == "__main__":
    main()
