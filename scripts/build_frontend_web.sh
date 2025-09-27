#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR/frontend"

if ! command -v flutter >/dev/null 2>&1; then
  echo "Flutter not found. Please install Flutter SDK and ensure it is on PATH."
  exit 1
fi

API_BASE_URL="${API_BASE_URL:-}"
if [[ -z "$API_BASE_URL" ]]; then
  echo "Usage: API_BASE_URL=https://<backend>/api/v1 scripts/build_frontend_web.sh"
  exit 1
fi

flutter pub get
flutter build web --release --web-renderer canvaskit --dart-define=API_BASE_URL=$API_BASE_URL

echo "Build completed: $ROOT_DIR/frontend/build/web"
