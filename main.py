"""
main.py — Entry point and orchestrator.
S: Wires components together; does not contain business logic itself.
D: All dependencies constructed here and injected into consumers.
"""
import threading, time, getpass

from installer  import ensure_dependencies
ensure_dependencies()

from config     import PORT, TOKEN, CMD_TIMEOUT, MAX_HISTORY, TUNNEL_KEEPALIVE
from history    import CommandHistory
from executor   import ShellExecutor
from api_routes import create_app
from tunnel     import BridgeTunnel
from telegram   import send_bridge_notifications, normalize_chat_id
from display    import (
    print_startup, print_connection_info,
    print_error, print_status_table,
)

_O   = "\033[0m"
_B   = "\033[1m"
_DIM = "\033[2m"
_GRN = "\033[92m"
_ORG = "\033[38;5;208m"


def _ask(prompt: str, secret: bool = False) -> str:
    print(f"{_ORG}{prompt}{_O}", end=" ", flush=True)
    if secret:
        return getpass.getpass("")
    return input()


def _ask_telegram() -> tuple[str, str] | tuple[None, None]:
    """
    Запрашивает токен бота и chat_id.
    Если оба пустые — Telegram-уведомления пропускаются.
    """
    print(f"\n{_DIM}── Telegram-уведомления ──────────────────{_O}")
    print(f"{_DIM}(Enter чтобы пропустить){_O}\n")

    bot_token = _ask("Bot token:", secret=True).strip()
    if not bot_token:
        print(f"{_DIM}Telegram пропущен.{_O}\n")
        return None, None

    chat_id_raw = _ask("Chat ID (например: 123456789 или -100...):")
    if not chat_id_raw.strip():
        print(f"{_DIM}Telegram пропущен.{_O}\n")
        return None, None

    try:
        chat_id = normalize_chat_id(chat_id_raw)
    except ValueError as e:
        print(f"\033[91m✗ {e}{_O}\n")
        return None, None

    print(f"{_GRN}✓ chat_id: {chat_id}{_O}\n")
    return bot_token, chat_id


def main() -> None:
    print_startup(PORT)

    tg_token, tg_chat = _ask_telegram()

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
        clean_url = url.rstrip("/")
        print_connection_info(clean_url, TOKEN)

        if tg_token and tg_chat:
            print(f"{_DIM}Отправляю в Telegram...{_O}")
            ok, err = send_bridge_notifications(tg_token, tg_chat, clean_url, TOKEN)
            if ok:
                print(f"{_GRN}✓ Telegram: 2 сообщения отправлены{_O}\n")
            else:
                print(f"\033[91m✗ Telegram: {err}{_O}\n")

    BridgeTunnel(PORT, _on_url).start_async()

    # ── Keep-alive loop (main thread) ───────────────────────────────────────────
    try:
        while True:
            time.sleep(TUNNEL_KEEPALIVE)
            recent = history.tail(8)
            if recent:
                print_status_table(recent)
    except KeyboardInterrupt:
        print(f"\n{_DIM}Мост остановлен.{_O}\n")


if __name__ == "__main__":
    main()
