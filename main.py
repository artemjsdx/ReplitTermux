import os, sys, signal, threading, time, getpass, subprocess
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
_RED = "\033[91m"
_ORG = "\033[38;5;208m"

# Глобальный реестр дочерних процессов для cleanup
_watchdog_proc: "subprocess.Popen | None" = None
_tunnel_proc:   "subprocess.Popen | None" = None
_shutdown_event = threading.Event()


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
    """Запускает watchdog.py как независимый процесс (отвязан от терминала)."""
    global _watchdog_proc
    wd = _BRIDGE_DIR / "watchdog.py"
    if not wd.exists():
        return
    # Убиваем предыдущий watchdog
    subprocess.run(
        "pkill -f \"python.*watchdog\\.py\" 2>/dev/null;"
        " pkill -f \"python3.*watchdog\\.py\" 2>/dev/null",
        shell=True,
    )
    time.sleep(0.4)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["RT_NONINTERACTIVE"] = "1"
    _watchdog_proc = subprocess.Popen(
        [sys.executable, str(wd)],
        cwd=str(_BRIDGE_DIR),
        env=env,
        stdout=open(str(_BRIDGE_DIR / "watchdog.log"), "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )


def _cleanup(signum=None, frame=None):
    """Корректное завершение: убиваем watchdog, туннель, освобождаем порт."""
    if _shutdown_event.is_set():
        return   # уже выполняется
    _shutdown_event.set()
    print("\n{}Завершение...{}".format(_DIM, _O))

    # 1. Останавливаем watchdog — иначе он перезапустит мост
    subprocess.run(
        "pkill -f \"python.*watchdog\\.py\" 2>/dev/null;"
        " pkill -f \"python3.*watchdog\\.py\" 2>/dev/null",
        shell=True,
    )
    if _watchdog_proc is not None:
        try:
            _watchdog_proc.terminate()
        except Exception:
            pass

    # 2. Убиваем туннель (serveo ssh-процесс)
    subprocess.run("pkill -f \"ssh.*serveo\" 2>/dev/null", shell=True)
    if _tunnel_proc is not None:
        try:
            _tunnel_proc.terminate()
        except Exception:
            pass

    # 3. Освобождаем порт принудительно
    subprocess.run(
        "fuser -k {}/tcp 2>/dev/null".format(PORT),
        shell=True,
    )

    # 4. Удаляем bridge_url.txt чтобы watchdog не думал что мост жив
    try:
        (_BRIDGE_DIR / "bridge_url.txt").unlink(missing_ok=True)
    except Exception:
        pass

    print("{}✓ Мост остановлен, порт {} освобождён.{}\n".format(_GRN, PORT, _O))
    sys.exit(0)


def main():
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT,  _cleanup)   # Ctrl+C
    signal.signal(signal.SIGTERM, _cleanup)   # kill / watchdog SIGTERM
    # SIGTSTP (Ctrl+Z) — показываем предупреждение вместо suspend
    try:
        signal.signal(signal.SIGTSTP, lambda s, f: print(
            "\n{}Ctrl+Z отключён — используй Ctrl+C для остановки.{}".format(_ORG, _O)
        ))
    except (OSError, AttributeError):
        pass

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
    time.sleep(0.5)

    def _on_url(url):
        clean = url.rstrip("/")
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
        _start_watchdog_background()

    BridgeTunnel(PORT, _on_url).start_async()

    # Главный цикл — ждём пока не придёт сигнал завершения
    try:
        while not _shutdown_event.is_set():
            time.sleep(TUNNEL_KEEPALIVE)
            recent = history.tail(8)
            if recent:
                print_status_table(recent)
    except KeyboardInterrupt:
        _cleanup()


if __name__ == "__main__":
    main()
