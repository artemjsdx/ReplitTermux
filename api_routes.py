"""
api_routes.py — Flask REST API routes.
S: One responsibility — HTTP layer only; delegates work to executor / history / web_ui.
I: Routes depend only on the interfaces they need (executor.run, history.append, etc.).
"""
from __future__ import annotations
from pathlib    import Path
import time

from flask import Flask, request, jsonify

from .config   import TOKEN
from .executor import ShellExecutor
from .history  import CommandHistory, CommandRecord
from .display  import print_result
from .web_ui   import render_web_ui


def _auth_ok() -> bool:
    t = request.headers.get("X-Token") or request.args.get("token", "")
    return t == TOKEN


def _deny():
    return jsonify({"error": "Unauthorized — X-Token header required"}), 401


def create_app(executor: ShellExecutor, history: CommandHistory) -> Flask:
    app = Flask(__name__)

    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

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
            return jsonify({"error": "поле 'cmd' обязательно"}), 400

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
    def upload():
        if not _auth_ok():
            return _deny()
        data    = request.get_json(silent=True) or {}
        path    = data.get("path", "")
        content = data.get("content", "")
        if not path:
            return jsonify({"error": "поле 'path' обязательно"}), 400
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return jsonify({"ok": True, "path": str(p)})
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

    @app.route("/")
    def web():
        if not _auth_ok():
            return _deny()
        return render_web_ui(TOKEN, history.tail(30))

    return app
