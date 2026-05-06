"""
telegram.py — Отправка сообщений через Telegram Bot API.
S: Одна ответственность — взаимодействие с Telegram.
"""
from __future__ import annotations
import re, urllib.request, urllib.parse, json


# ── helpers ────────────────────────────────────────────────────────────────────

def normalize_chat_id(raw: str) -> str:
    """
    Приводит chat_id к корректному виду.
    Поддерживает: 123456789 / -123456789 / -100123456789 / 100123456789
    Супергруппы/каналы всегда должны начинаться с -100.
    """
    raw = raw.strip()
    digits = re.sub(r"[^\d]", "", raw)
    negative = raw.startswith("-")

    if not digits:
        raise ValueError(f"Некорректный chat_id: {raw!r}")

    # Если пользователь передал -100... или 100... (супергруппа)
    if digits.startswith("100") and len(digits) > 10:
        return f"-{digits}"
    if negative:
        return f"-{digits}"
    return digits


def _api(bot_token: str, method: str, payload: dict) -> dict:
    url  = f"https://api.telegram.org/bot{bot_token}/{method}"
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def send_message(
    bot_token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
) -> dict:
    return _api(bot_token, "sendMessage", {
        "chat_id":                   chat_id,
        "text":                      text,
        "parse_mode":                parse_mode,
        "disable_web_page_preview":  disable_web_page_preview,
    })


# ── готовые сообщения ──────────────────────────────────────────────────────────

def _msg_bridge_info(url: str, token: str) -> str:
    web = f"{url}/?token={token}"
    return (
        "🔗 <b>ReplitTermux — мост активен</b>\n\n"
        f"<b>URL:</b>\n<code>{url}</code>\n\n"
        f"<b>Token:</b>\n<code>{token}</code>\n\n"
        f"<b>Веб-интерфейс:</b>\n{web}"
    )


def _msg_ai_prompt(url: str, token: str) -> str:
    prompt = (
        f"У тебя есть доступ к ReplitTermux — REST API, который выполняет команды "
        f"в реальном Termux на Android-устройстве.\n\n"
        f"BASE URL: {url}\n"
        f"Токен авторизации: {token}\n"
        f"Заголовок для всех запросов: X-Token: {token}\n\n"
        f"=== ДОСТУПНЫЕ ЭНДПОИНТЫ ===\n\n"
        f"1. GET /ping\n"
        f"   Проверка доступности (без токена).\n\n"
        f"2. POST /run\n"
        f"   Выполнить shell-команду.\n"
        f"   Body: {{\"cmd\": \"ls ~\"}}\n"
        f"   Возвращает: {{cmd, out, code, elapsed, ts}}\n\n"
        f"3. GET /history?n=50\n"
        f"   Последние N выполненных команд.\n\n"
        f"4. POST /upload\n"
        f"   Записать файл на устройство.\n"
        f"   Body: {{\"path\": \"~/file.txt\", \"content\": \"текст\"}}\n\n"
        f"5. GET /download?path=~/file.txt\n"
        f"   Прочитать файл с устройства.\n\n"
        f"=== ПРИМЕР ЗАПРОСА ===\n\n"
        f'curl -X POST {url}/run \\\n'
        f'  -H "X-Token: {token}" \\\n'
        f'  -H "Content-Type: application/json" \\\n'
        f"  -d '{{\"cmd\":\"uname -a\"}}'\n\n"
        f"=== ЧТО УМЕЕТ МОСТ ===\n\n"
        f"• Выполнять любые команды Linux/Android\n"
        f"• Читать и писать файлы на устройство\n"
        f"• Управлять приложениями через Termux\n"
        f"• Устанавливать пакеты (pkg install / pip install)\n"
        f"• Запускать скрипты Python, Node, Bash\n"
        f"• Получать историю выполненных команд\n\n"
        f"Используй /run для каждого действия. Всегда проверяй code == 0 (успех) "
        f"или != 0 (ошибка). Таймаут команды — 60 секунд."
    )
    return (
        "🤖 <b>Промпт для ИИ-агента</b>\n\n"
        "<blockquote expandable>"
        + prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        + "</blockquote>"
    )


def send_bridge_notifications(
    bot_token: str,
    chat_id: str,
    url: str,
    token: str,
) -> tuple[bool, str]:
    """
    Отправляет 2 сообщения в Telegram.
    Возвращает (success, error_message).
    """
    cid = normalize_chat_id(chat_id)
    try:
        send_message(bot_token, cid, _msg_bridge_info(url, token))
        send_message(bot_token, cid, _msg_ai_prompt(url, token))
        return True, ""
    except Exception as exc:
        return False, str(exc)
