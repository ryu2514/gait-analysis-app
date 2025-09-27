#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"
URL="http://127.0.0.1:${PORT}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "[tunnel] cloudflared is not installed."
  echo "[tunnel] macOS: brew install cloudflared"
  echo "[tunnel] Docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation"
  exit 1
fi

echo "[tunnel] Publishing ${URL} via Cloudflare Tunnel..."
echo "[tunnel] Press Ctrl+C to stop."
exec cloudflared tunnel --url "${URL}"

