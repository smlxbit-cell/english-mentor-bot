#!/bin/bash
# First-time setup on Ubuntu 22.04 (Yandex Cloud VM).
# Run as root: bash deploy/server_setup.sh
set -euo pipefail

APP_USER=mentor
APP_HOME=/home/$APP_USER
APP_DIR=$APP_HOME/english-mentor-bot
REPO_URL="${REPO_URL:-https://github.com/smlxbit-cell/english-mentor-bot.git}"

echo "==> System packages"
apt-get update
apt-get install -y git python3 python3-venv python3-pip build-essential

echo "==> App user"
id "$APP_USER" &>/dev/null || useradd -m -s /bin/bash "$APP_USER"
mkdir -p "$APP_HOME/logs"
chown -R "$APP_USER:$APP_USER" "$APP_HOME"

echo "==> Clone repo (as $APP_USER)"
if [ ! -d "$APP_DIR/.git" ]; then
  sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
fi

echo "==> Python venv + dependencies"
sudo -u "$APP_USER" bash -c "
  cd '$APP_DIR'
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
"

echo "==> Next steps (manual):"
echo "  1. Copy .env from your PC to $APP_DIR/.env"
echo "  2. Copy media/spirit/ to $APP_DIR/media/spirit/"
echo "  3. sudo -u $APP_USER bash -c 'cd $APP_DIR && .venv/bin/python manage.py migrate'"
echo "  4. sudo -u $APP_USER bash -c 'cd $APP_DIR && .venv/bin/python manage.py seed_content'"
echo "  5. sudo -u $APP_USER bash -c 'cd $APP_DIR && .venv/bin/python manage.py sync_spirit_media --force'"
echo "  6. cp $APP_DIR/deploy/english-mentor-bot.service /etc/systemd/system/"
echo "  7. systemctl daemon-reload && systemctl enable --now english-mentor-bot"
echo "  8. crontab -u $APP_USER -e  (paste deploy/cron.example)"
