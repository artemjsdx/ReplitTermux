"""
main.py — Entry point and orchestrator.
S: Wires components together; does not contain business logic itself.
D: All dependencies constructed here and injected into consumers.
"""
import threading, time

from installer  import ensure_dependencies
ensure_dependencies()   # must run before any rich/flask imports

from config     import PORT, TOKEN, CMD_TIMEOUT, MAX_HISTORY, TUNNEL_KEEPALIVE
from history    import CommandHistory
from executor   import ShellExecutor
from api_routes import create_app
from tunnel     import BridgeTunnel
from display    import (
    console, print_startup, print_connection_info,
    print_error, print_status_table,
)


def main() -> None:
    print_startup(PORT)

    history  = CommandHistory(max_size=MAX_HISTORY)
    executor = ShellExecutor(timeout=CMD_TIMEOUT)
    app      = create_app(executor, history)

    # ── Flask in background thread ──────────────────────────────────────────────
    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0", port=PORT, debug=False,
            use_reloader=False, threaded=True,
        ),
        daemon=True,
    ).start()
    time.sleep(0.4)

    # ── Tunnel ─────────────────────────────────────────────────────────────────
    def _on_url(url: str) -> None:
        print_connection_info(url.rstrip("/"), TOKEN)

    BridgeTunnel(PORT, _on_url).start_async()

    # ── Keep-alive loop (main thread) ───────────────────────────────────────────
    try:
        while True:
            time.sleep(TUNNEL_KEEPALIVE)
            recent = history.tail(8)
            if recent:
                print_status_table(recent)
    except KeyboardInterrupt:
        console.print("\n  [dim]Мост остановлен.[/dim]\n")


if __name__ == "__main__":
    main()
