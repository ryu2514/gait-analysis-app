#!/usr/bin/env bash
set -euo pipefail

# Lightweight demo launcher for the backend API
# - Creates venv if missing
# - Installs dependencies
# - Starts uvicorn with LIGHT_MODE=1 in background

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/venv"
LOG_FILE="$ROOT_DIR/.demo_server.log"
HOST="127.0.0.1"
PORT="8000"

choose_port() {
  local p=$1
  while lsof -iTCP:"$p" -sTCP:LISTEN -n -P >/dev/null 2>&1; do
    p=$((p+1))
  done
  echo "$p"
}

echo "[demo] Ensuring virtualenv..."
if [ ! -x "$VENV_DIR/bin/python" ]; then
  python3 -m venv "$VENV_DIR"
fi

echo "[demo] Installing dependencies (this may take a moment)..."
"$VENV_DIR/bin/pip" install -q -r "$ROOT_DIR/requirements.txt" >/dev/null
# redis is imported on module load in performance_config; make sure it's present
"$VENV_DIR/bin/pip" install -q redis==5.0.1 >/dev/null || true

PORT=$(choose_port "$PORT")
URL="http://$HOST:$PORT"

echo "[demo] Starting server in LIGHT_MODE on $URL ..."
(
  export LIGHT_MODE=1
  export DISABLE_TASK_QUEUE=1
  exec "$VENV_DIR/bin/uvicorn" main:app --host "$HOST" --port "$PORT" --log-level info
) >"$LOG_FILE" 2>&1 &

PID=$!
sleep 1

echo -n "[demo] Waiting for health endpoint"
for i in $(seq 1 60); do
  if curl -s "${URL}/api/v1/health" >/dev/null; then
    READY=1
    break
  fi
  echo -n "."
  sleep 1
done
echo

if [ "${READY:-0}" -eq 1 ] && ps -p "$PID" >/dev/null 2>&1; then
  echo "[demo] Server PID: $PID"
  echo "[demo] Logs: $LOG_FILE"
  echo "[demo] Ready URL: $URL"
  exit 0
fi

echo "[demo] Failed to become ready. Recent logs:"
tail -n 200 "$LOG_FILE" || true
exit 1
