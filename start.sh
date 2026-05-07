#!/data/data/com.termux/files/usr/bin/bash
# start.sh — запустить ReplitTermux мост + watchdog одной командой
# Использование: bash start.sh

BRIDGE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BRIDGE_DIR"

echo "=== ReplitTermux Launcher ==="

# Убиваем старые процессы
pkill -f 'python.*most\.py' 2>/dev/null
pkill -f 'python3.*watchdog\.py' 2>/dev/null
sleep 1

# Запускаем watchdog в фоне через nohup (он сам запустит мост)
nohup python3 watchdog.py >> watchdog.log 2>&1 &
WD_PID=$!
echo "Watchdog PID=$WD_PID"
echo $WD_PID > watchdog.pid

# Ждём URL
echo "Waiting for bridge URL..."
for i in $(seq 1 45); do
  sleep 2
  if [ -f bridge_url.txt ]; then
    URL=$(cat bridge_url.txt)
    if [ -n "$URL" ]; then
      echo ""
      echo "======================================"
      echo "  Bridge URL : $URL"
      TOKEN=$(cat ~/.replittermux.token 2>/dev/null || echo '(check bridge.log)')
      echo "  Token      : $TOKEN"
      echo "  Watchdog   : PID=$WD_PID"
      echo "======================================"
      echo ""
      echo "Agent prompt:"
      echo "BASE URL: $URL"
      echo "Token: $TOKEN"
      echo "Header: X-Token: $TOKEN"
      exit 0
    fi
  fi
  printf "."
done

echo ""
echo "URL not detected after 90s — check bridge.log:"
tail -20 bridge.log
