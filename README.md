# ReplitTermux

**Мост между Replit-агентом и твоим Android Termux.**

Запускаешь на телефоне — получаешь публичный URL и токен — вставляешь в чат Replit-агента — и агент может выполнять команды прямо в твоём Termux, читать/писать файлы, проверять состояние устройства.

---

## Как это работает

```
Replit-агент
    │  POST /run  {"cmd":"..."}  X-Token: <token>
    ▼
serveo.net (SSH-туннель)
    │
    ▼
Termux  →  Flask API  →  subprocess  →  ответ
```

1. Запускаешь `python -m ReplitTermux` на Android (Termux)
2. Скрипт поднимает локальный API-сервер на порту 7474
3. Пробивает бесплатный SSH-туннель через serveo.net (fallback: localhost.run)
4. Показывает публичный **URL** и **токен** — копируешь и отправляешь агенту
5. Агент шлёт HTTP-запросы → команды выполняются прямо на телефоне

---

## Быстрый старт

```bash
# Установка
pkg install python openssh
pip install flask rich requests

# Запуск
python -m ReplitTermux
```

Или клонируй и запускай:

```bash
git clone https://github.com/YOUR_USER/ReplitTermux.git
cd ReplitTermux
python -m ReplitTermux
```

После запуска в терминале появится:

```
─────────────────── ✓ Мост готов ───────────────────
  URL   https://xxxxx.serveo.net
  Token rt-xxxxxxxxxxxxxxxx
  Web   https://xxxxx.serveo.net/?token=rt-...

  curl -X POST https://xxxxx.serveo.net/run \
    -H 'X-Token: rt-...' \
    -H 'Content-Type: application/json' \
    -d '{"cmd":"uname -a"}'
─────────────────────────────────────────────────────
```

Скопируй URL + токен и отправь Replit-агенту.

---

## API

Все запросы требуют заголовок `X-Token: <token>` (или query-параметр `?token=...`).

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/ping` | Проверка доступности (без токена) |
| POST | `/run` | Выполнить команду (JSON: `{"cmd": "..."}`) |
| GET | `/history?n=50` | Последние N выполненных команд |
| POST | `/upload` | Записать файл (`{"path": "...", "content": "..."}`) |
| GET | `/download?path=...` | Прочитать файл с устройства |
| GET | `/?token=...` | Веб-интерфейс в браузере |

### Примеры для Replit-агента

```bash
# Проверка
curl https://xxxxx.serveo.net/ping

# Выполнить команду
curl -X POST https://xxxxx.serveo.net/run \
  -H "X-Token: rt-..." \
  -H "Content-Type: application/json" \
  -d '{"cmd":"ls ~"}'

# Записать файл на устройство
curl -X POST https://xxxxx.serveo.net/upload \
  -H "X-Token: rt-..." \
  -H "Content-Type: application/json" \
  -d '{"path":"~/test.txt","content":"Hello from Replit!"}'

# Прочитать файл
curl "https://xxxxx.serveo.net/download?path=~/test.txt&token=rt-..."
```

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `RT_PORT` | `7474` | Порт локального сервера |
| `RT_TOKEN` | авто (uuid) | Токен авторизации (зафикси для постоянства) |
| `RT_CMD_TIMEOUT` | `60` | Таймаут выполнения команды (сек) |
| `RT_MAX_HISTORY` | `200` | Размер лога команд |
| `RT_TUNNEL_KEEPALIVE` | `30` | Интервал обновления статуса (сек) |

Зафиксировать токен постоянным:
```bash
export RT_TOKEN="мой-секретный-токен"
python -m ReplitTermux
```

---

## Архитектура (SOLID)

```
ReplitTermux/
├── config.py       # S — конфигурация (только настройки)
├── installer.py    # S — автоустановка зависимостей
├── history.py      # S — хранение лога команд
├── executor.py     # S — выполнение shell-команд
├── tunnel.py       # S/O/L/D — SSH-туннели (провайдеры, расширяемо)
├── display.py      # S — весь Rich-вывод в терминале
├── api_routes.py   # S/I — HTTP-роуты Flask
├── web_ui.py       # S — HTML веб-интерфейс
├── main.py         # D — сборка и запуск
├── __init__.py
└── __main__.py     # python -m ReplitTermux
```

**Принципы:**
- **S** — каждый модуль делает одно и только одно
- **O** — добавить новый туннель-провайдер можно без изменения существующего кода
- **L** — `ServeoTunnel` и `LocalhostRunTunnel` взаимозаменяемы через `TunnelProvider`
- **I** — роуты зависят только от нужных им интерфейсов
- **D** — зависимости собираются в `main.py` и передаются через конструкторы

---

## Безопасность

- Все API-запросы требуют токен — без него возвращается `401 Unauthorized`
- Токен генерируется случайным образом при каждом запуске (или задаётся через `RT_TOKEN`)
- Рекомендуется запускать только тогда, когда мост нужен — и останавливать по завершении

---

## Требования

- Android + **Termux**
- `pkg install openssh python`
- `pip install flask rich requests`

---

## Лицензия

MIT
