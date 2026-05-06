"""
config_store.py — Сохранение и загрузка пользовательских настроек.
S: Одна ответственность — персистентность конфига.
"""
import json, os
from pathlib import Path

_CONFIG_PATH = Path.home() / ".replittermux.conf"


def load() -> dict:
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save(data: dict) -> None:
    try:
        _CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        _CONFIG_PATH.chmod(0o600)  # только владелец может читать
    except Exception:
        pass  # не блокируем запуск если сохранить не вышло


def get(key: str, default: str = "") -> str:
    return load().get(key, default)


def set_key(key: str, value: str) -> None:
    data = load()
    data[key] = value
    save(data)
