#!/bin/bash
# Cloudflare WARP on Ubuntu — free way to reach api.telegram.org from RU datacenters.
# Run on Yandex VM: sudo bash deploy/setup_warp.sh
set -euo pipefail

if curl -fsI --max-time 10 https://api.telegram.org >/dev/null 2>&1; then
  echo "Telegram already reachable — WARP not needed."
  exit 0
fi

echo "==> Install Cloudflare WARP"
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
  | gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" \
  > /etc/apt/sources.list.d/cloudflare-client.list
apt-get update
apt-get install -y cloudflare-warp

echo "==> Connect WARP"
warp-cli registration new 2>/dev/null || warp-cli register 2>/dev/null || true
warp-cli mode warp 2>/dev/null || true
warp-cli connect

sleep 3
echo "==> Test Telegram"
if curl -fsI --max-time 20 https://api.telegram.org; then
  echo ""
  echo "SUCCESS: Telegram is reachable. Restart the bot:"
  echo "  systemctl restart english-mentor-bot"
else
  echo "WARP did not help. Use SOCKS proxy — see docs/TELEGRAM_PROXY_YANDEX.md"
  exit 1
fi
