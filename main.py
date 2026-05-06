"""
main.py — Entry point and orchestrator.
S: Wires components together; does not contain business logic itself.
D: All dependencies constructed here and injected into consumers.
"""
import threading, time, getpass

from installer    import ensure_dependencies
ensure_dependencies()

from config       import PORT, TOKEN, CMD_TIMEOUT, MAX_HISTORY, TUNNEL_KEEPALIVE
from history      import CommandHistory
from executor     import ShellExecutor
from api_routes   import create_app
from tunnel       import BridgeTunnel
from telegram     import send_bridge_notifications, normalize_chat_id
from config_store import load as cfg_load, save as cfg_save
from display      import (
    print_startup, print_connection_info, print_bridge_ready,
    print_error, print_status_table,
)

_O   = "\033[0m"
_DIM = "\033[2m"
_GRN = "\033[92m"
_YEL = "\033[93m"
_RED = "\033[91m"
_ORG = "\033[38;5;208m"


def _ask(prompt: str, secret: bool = False) -> str:
    print(f"{_ORG}{prompt}{_O}", end=" ", flush=True)
    return getpass.getpass("") if secret else input()


def _ask_telegram() -> tuple[str, str] | tuple[None, None]:
    cfg = cfg_load()
    saved_token = cfg.get("bot_token", "")
    saved_chat  = cfg.get("chat_id", "")

    print(f"{_DIM}── Telegram-уведомления ──────────────────{_O}")

    if saved_token and saved_chat:
        print(f"{_GRN}Сохранённый чат: {saved_chat}{_O}")
        print(f"{_DIM}Enter — использовать сохранённое, или введи новые данные.{_O}\n")

        new_chat = _ask("Chat ID [сохранённый]:")
        if not new_chat.strip():
            # используем сохранённое
            return saved_token, saved_chat

        # введён новый chat_id — спросим и токен
        new_token = _ask("Bot token:", secret=True).strip()
        if not new_token:
            new_token = saved_token   # токен оставляем старый

        try:
            chat_id = normalize_chat_id(new_chat)
        except ValueError as e:
            print(f"{_RED}✗ {e}{_O}\n")
            return None, None

        cfg_save({"bot_token": new_token, "chat_id": chat_id})
        print(f"{_GRN}✓ Сохранено. chat_id: {chat_id}{_O}\n")
        return new_token, chat_id

    # нет сохранённых данных
    print(f"{_DIM}(Enter чтобы пропустить){_O}\n")
    bot_token = _ask("Bot token:", secret=True).strip()
    if not bot_token:
        print(f"{_DIM}Telegram пропущен.{_O}\n")
        return None, None

    chat_id_raw = _ask("Chat ID:")
    if not chat_id_raw.strip():
        print(f"{_DIM}Telegram пропущен.{_O}\n")
        return None, None

    try:
        chat_id = normalize_chat_id(chat_id_raw)
    except ValueError as e:
        print(f"{_RED}✗ {e}{_O}\n")
        return None, None

    cfg_save({"bot_token": bot_token, "chat_id": chat_id})
    print(f"{_GRN}✓ Сохранено. chat_id: {chat_id}{_O}\n")
    return bot_token, chat_id


def main() -> None:
    print_startup(PORT)

    tg_token, tg_chat = _ask_telegram()

    history  = CommandHistory(max_size=MAX_HISTORY)
    executor = ShellExecutor(timeout=CMD_TIMEOUT)
    app      = create_app(executor, history)

    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0", port=PORT, debug=False,
            use_reloader=False, threaded=True,
        ),
        daemon=True,
    ).start()
    time.sleep(0.4)

    def _on_url(url: str) -> None:
        clean = url.rstrip("/")

        if tg_token and tg_chat:
            print(f"{_DIM}Отправляю в Telegram...{_O}")
            ok, err = send_bridge_notifications(tg_token, tg_chat, clean, TOKEN)
            if ok:
                print(f"{_GRN}✓ Telegram: 2 сообщения отправлены{_O}")
                print_bridge_ready()
            else:
                print(f"{_RED}✗ Telegram: {err}{_O}")
                print_connection_info(clean, TOKEN)
        else:
            print_connection_info(clean, TOKEN)

    BridgeTunnel(PORT, _on_url).start_async()

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
