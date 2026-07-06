# Telegram с Yandex Cloud (когда `curl api.telegram.org` — timeout)

Yandex VM **не видит** Telegram напрямую. Два способа — пробуйте **по порядку**.

---

## Способ 1 — Cloudflare WARP (бесплатно, без второго сервера)

На сервере по SSH:

```bash
cd /home/mentor/english-mentor-bot
sudo git pull
sudo bash deploy/setup_warp.sh
```

Если в конце **SUCCESS** — перезапустите бота:

```bash
sudo systemctl restart english-mentor-bot
sudo systemctl status english-mentor-bot
```

Проверка:

```bash
curl -I --max-time 15 https://api.telegram.org
```

Должен ответить быстро (не timeout).

**В `.env` прокси не нужен** — весь исходящий трафик идёт через WARP.

---

## Способ 2 — SOCKS-прокси (если WARP не помог)

Нужен **маленький VPS за рубежом** (только как прокси, ~€3–4/мес Hetzner) **или** платный SOCKS.

### На прокси-сервере (EU)

```bash
sudo apt update && sudo apt install -y microsocks
# только с IP вашей Yandex VM (158.160.x.x):
microsocks -i 0.0.0.0 -p 1080 -u mentor -P ВАШ_ПАРОЛЬ
```

Откройте порт **1080** только для IP Yandex VM.

### На Yandex VM — в `.env`

```bash
sudo nano /home/mentor/english-mentor-bot/.env
```

Добавьте:

```env
TELEGRAM_PROXY=socks5://mentor:ВАШ_ПАРОЛЬ@IP_ПРОКСИ_СЕРВЕРА:1080
```

### Установить поддержку SOCKS и обновить код

```bash
cd /home/mentor/english-mentor-bot
sudo -u mentor git pull
sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && .venv/bin/pip install "httpx[socks]"'
sudo systemctl restart english-mentor-bot
```

---

## После любого способа

1. **Не запускайте** `runbot` на ПК.
2. Telegram → `/start`
3. Логи:

```bash
sudo journalctl -u english-mentor-bot -n 20 --no-pager
```

Не должно быть `TimedOut` / `FAILURE`.

---

## Spirit (эмоции) — если не делали

```bash
sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && .venv/bin/python manage.py sync_spirit_media --force --chat-id ВАШ_TELEGRAM_ID'
```

---

## Кратко

| Шаг | Действие |
|-----|----------|
| 1 | `sudo bash deploy/setup_warp.sh` |
| 2 | `systemctl restart english-mentor-bot` |
| 3 | `/start` в Telegram |
| Если WARP fail | SOCKS + `TELEGRAM_PROXY` в `.env` |

ПК и сон ноутбука **не важны** — бот на Yandex, проблема была только сеть → Telegram.
