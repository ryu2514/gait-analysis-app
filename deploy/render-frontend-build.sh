#!/usr/bin/env bash
set -euo pipefail

# Render Static Site build script for Flutter Web
# - Installs Flutter SDK (shallow clone)
# - Runs pub get
# - Builds web with optional API_BASE_URL

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
FRONTEND_DIR="$ROOT_DIR/frontend"
FLUTTER_CHANNEL="stable"
FLUTTER_VERSION=""  # optional pin

echo "[Build] Using FRONTEND_DIR=$FRONTEND_DIR"
cd "$FRONTEND_DIR"

echo "[Build] Fetching Flutter SDK ($FLUTTER_CHANNEL) ..."
git clone --depth 1 --branch "$FLUTTER_CHANNEL" https://github.com/flutter/flutter.git "$FRONTEND_DIR/.flutter"
export PATH="$FRONTEND_DIR/.flutter/bin:$PATH"

if [[ -n "$FLUTTER_VERSION" ]]; then
  echo "[Build] Pinning Flutter to $FLUTTER_VERSION"
  pushd "$FRONTEND_DIR/.flutter" >/dev/null
  git fetch --depth 1 origin "$FLUTTER_VERSION"
  git checkout "$FLUTTER_VERSION"
  popd >/dev/null
fi

echo "[Build] Flutter doctor (summary)"
flutter --version

echo "[Build] Enabling web support"
flutter config --enable-web

echo "[Build] Getting packages"
flutter pub get

# API_BASE_URL is passed from Render Static Site env var
API_BASE_URL_FLAG=""
if [[ -n "${API_BASE_URL:-}" ]]; then
  echo "[Build] Using API_BASE_URL=$API_BASE_URL"
  API_BASE_URL_FLAG="--dart-define=API_BASE_URL=$API_BASE_URL"
else
  echo "[Build] API_BASE_URL not set. Using default in code."
fi

echo "[Build] Building Flutter Web (release)"
flutter build web \
  --release \
  --web-renderer canvaskit \
  $API_BASE_URL_FLAG

echo "[Build] Build completed. Output: $FRONTEND_DIR/build/web"

