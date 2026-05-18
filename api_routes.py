from __future__ import annotations
from pathlib import Path
import time, logging, base64

from flask import Flask, request, jsonify

from config   import TOKEN
from executor import ShellExecutor
from history  import CommandHistory, CommandRecord
from display  import print_result
from web_ui   import render_web_ui

_BRIDGE_DIR = Path(__file__).parent.resolve()


def _auth_ok():
    t = request.headers.get("X-Token") or request.args.get("token", "")
    return t == TOKEN


def _deny():
    return jsonify({"error": "Unauthorized -- X-Token header required"}), 401


def create_app(executor, history):
    app = Flask(__name__)

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.logger.setLevel(logging.ERROR)
    app.config["JSON_AS_ASCII"] = False
    try:
        import flask.cli
        flask.cli.show_server_banner = lambda *a, **kw: None
    except Exception:
        pass

    @app.route("/ping")
    def ping():
        return jsonify({"ok": True, "ts": time.time()})

    @app.route("/run", methods=["POST"])
    def run_cmd():
        if not _auth_ok():
            return _deny()
        data = request.get_json(silent=True) or {}
        cmd  = str(data.get("cmd", "")).strip()
        if not cmd:
            return jsonify({"error": "поле cmd обязательно"}), 400
        record = executor.run(cmd)
        history.append(record)
        print_result(record)
        return jsonify(record.to_dict())

    @app.route("/history")
    def get_history():
        if not _auth_ok():
            return _deny()
        n = int(request.args.get("n", 50))
        return jsonify([r.to_dict() for r in history.tail(n)])

    @app.route("/upload", methods=["POST"])
    def upload_file():
        if not _auth_ok():
            return _deny()
        data    = request.get_json(silent=True) or {}
        path    = data.get("path", "")
        content = data.get("content", "")
        if not path:
            return jsonify({"error": "поле path обязательно"}), 400
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return jsonify({"ok": True, "path": str(p)})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/upload_binary", methods=["POST"])
    def upload_binary():
        if not _auth_ok():
            return _deny()
        data        = request.get_json(silent=True) or {}
        path        = data.get("path", "")
        content_b64 = data.get("content_b64", "")
        if not path:
            return jsonify({"error": "поле path обязательно"}), 400
        if not content_b64:
            return jsonify({"error": "поле content_b64 обязательно"}), 400
        try:
            raw = base64.b64decode(content_b64)
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
            return jsonify({"ok": True, "path": str(p), "bytes": len(raw)})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/download")
    def download():
        if not _auth_ok():
            return _deny()
        path = request.args.get("path", "")
        if not path:
            return jsonify({"error": "path обязателен"}), 400
        try:
            content = Path(path).expanduser().read_text(encoding="utf-8")
            return jsonify({"path": path, "content": content})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/ctrl", methods=["POST"])
    def ctrl():
        if not _auth_ok():
            return _deny()
        data = request.get_json(silent=True) or {}
        cmd  = str(data.get("cmd", "")).strip().upper()
        if cmd not in ("RESTART", "UPDATE", "STOP"):
            return jsonify({"error": "Unknown cmd", "allowed": ["RESTART","UPDATE","STOP"]}), 400
        try:
            (_BRIDGE_DIR / "control.txt").write_text(cmd, encoding="utf-8")
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500
        return jsonify({"ok": True, "cmd": cmd, "msg": "Signal written -- watchdog acts in ~15s"})

    @app.route("/status")
    def status():
        if not _auth_ok():
            return _deny()
        url_file = _BRIDGE_DIR / "bridge_url.txt"
        url = url_file.read_text(encoding="utf-8").strip() if url_file.exists() else "unknown"
        wd_log = _BRIDGE_DIR / "watchdog.log"
        wd_tail = ""
        if wd_log.exists():
            lines_log = wd_log.read_text(encoding="utf-8").splitlines()
            wd_tail = "\n".join(lines_log[-10:])
        return jsonify({
            "ok": True,
            "bridge_url": url,
            "history_len": len(history),
            "watchdog_tail": wd_tail,
        })

    @app.route("/")
    def web():
        if not _auth_ok():
            return _deny()
        return render_web_ui(TOKEN, history.tail(30))

    return app
