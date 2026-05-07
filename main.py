import os, sys, threading, time, getpass, subprocess
from pathlib import Path

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

_BRIDGE_DIR = Path(__file__).parent.resolve()

_O   = "\033[0m"
_DIM = "\033[2m"
_GRN = "\033[92m"
_YEL = "\033[93m"
_RED = "\033[91m"
_ORG = "\033[38;5;208m"


def _ask(prompt, secret=False):
    print("{}{}{}".format(_ORG, prompt, _O), end=" ", flush=True)
    return getpass.getpass("") if secret else input()


def _ask_telegram():
    cfg         = cfg_load()
    saved_token = cfg.get("bot_token", "")
    saved_chat  = cfg.get("chat_id", "")
    print("{}── Telegram-уведомления ──────────────────{}".format(_DIM, _O))

    if saved_token and saved_chat:
        print("{}Сохранённый чат: {}{}".format(_GRN, saved_chat, _O))
        print("{}Enter — использовать сохранённое.{}\n".format(_DIM, _O))
        new_chat = _ask("Chat ID [сохранённый]:")
        if not new_chat.strip():
            return saved_token, saved_chat
        new_token = _ask("Bot token:", secret=True).strip() or saved_token
        try:
            chat_id = normalize_chat_id(new_chat)
        except ValueError as e:
            print("{}✗ {}{}\n".format(_RED, e, _O))
            return None, None
        cfg_save({"bot_token": new_token, "chat_id": chat_id})
        return new_token, chat_id

    print("{}(Enter чтобы пропустить){}\n".format(_DIM, _O))
    bot_token = _ask("Bot token:", secret=True).strip()
    if not bot_token:
        print("{}Telegram пропущен.{}\n".format(_DIM, _O))
        return None, None
    chat_id_raw = _ask("Chat ID:")
    if not chat_id_raw.strip():
        return None, None
    try:
        chat_id = normalize_chat_id(chat_id_raw)
    except ValueError as e:
        print("{}✗ {}{}\n".format(_RED, e, _O))
        return None, None
    cfg_save({"bot_token": bot_token, "chat_id": chat_id})
    return bot_token, chat_id


def _start_watchdog_background():
    """Запускает watchdog.py как независимый фоновый процесс (не привязан к терминалу)."""
    wd = _BRIDGE_DIR / "watchdog.py"
    if not wd.exists():
        return
    # Убиваем старый watchdog если был
    subprocess.run(
        "pkill -f 'python.*watchdog\.py' 2>/dev/null; pkill -f 'python3.*watchdog\.py' 2>/dev/null",
        shell=True,
    )
    time.sleep(0.5)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["RT_NONINTERACTIVE"] = "1"
    log_handle = open(str(_BRIDGE_DIR / "watchdog.log"), "a", encoding="utf-8")
    subprocess.Popen(
        [sys.executable, str(wd)],
        cwd=str(_BRIDGE_DIR),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,   # отвязываем от текущего терминала
        close_fds=True,
    )


def main():
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

    def _on_url(url):
        clean = url.rstrip("/")
        # Пишем URL чтобы watchdog мог сообщить о нём после авторестарта
        try:
            (_BRIDGE_DIR / "bridge_url.txt").write_text(clean, encoding="utf-8")
        except Exception:
            pass
        if tg_token and tg_chat:
            print("{}Отправляю в Telegram...{}".format(_DIM, _O))
            ok, err = send_bridge_notifications(tg_token, tg_chat, clean, TOKEN)
            if ok:
                print("{}✓ Telegram отправлен{}".format(_GRN, _O))
                print_bridge_ready()
            else:
                print("{}✗ Telegram: {}{}".format(_RED, err, _O))
                print_connection_info(clean, TOKEN)
        else:
            print_connection_info(clean, TOKEN)
        # Запускаем watchdog в фоне ПОСЛЕ того как мост поднялся
        _start_watchdog_background()

    BridgeTunnel(PORT, _on_url).start_async()

    try:
        while True:
            time.sleep(TUNNEL_KEEPALIVE)
            recent = history.tail(8)
            if recent:
                print_status_table(recent)
    except KeyboardInterrupt:
        print("\n{}Мост остановлен.{}\n".format(_DIM, _O))


if __name__ == "__main__":
    main()
