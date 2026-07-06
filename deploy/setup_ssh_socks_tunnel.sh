#!/bin/bash
# SOCKS5 on Yandex VM via SSH tunnel to any server outside RU (Hetzner, etc.).
#
# On EU VPS you need ONLY SSH login — no extra software.
#
# 1) Copy your SSH key to EU VPS (one time):
#      ssh-copy-id -i /home/mentor/.ssh/id_ed25519 ubuntu@EU_VPS_IP
#
# 2) On Yandex VM:
#      sudo bash deploy/setup_ssh_socks_tunnel.sh ubuntu@EU_VPS_IP
#
# 3) Add to .env:
#      TELEGRAM_PROXY=socks5://127.0.0.1:1080
#
# 4) pip install "httpx[socks]" && systemctl restart english-mentor-bot
set -euo pipefail

REMOTE="${1:-}"
if [ -z "$REMOTE" ]; then
  echo "Usage: sudo bash deploy/setup_ssh_socks_tunnel.sh user@EU_VPS_IP"
  exit 1
fi

apt-get update
apt-get install -y autossh

mkdir -p /etc/systemd/system

cat > /etc/systemd/system/telegram-socks-tunnel.service <<EOF
[Unit]
Description=SSH SOCKS5 tunnel for Telegram API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mentor
ExecStart=/usr/bin/autossh -M 0 -N -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -D 127.0.0.1:1080 ${REMOTE}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now telegram-socks-tunnel.service
sleep 2

if curl -fsI --max-time 20 --proxy socks5://127.0.0.1:1080 https://api.telegram.org; then
  echo ""
  echo "SUCCESS. Add to /home/mentor/english-mentor-bot/.env:"
  echo "  TELEGRAM_PROXY=socks5://127.0.0.1:1080"
else
  echo "Tunnel up but Telegram still fails — check EU VPS SSH and firewall."
  journalctl -u telegram-socks-tunnel -n 20 --no-pager
  exit 1
fi
