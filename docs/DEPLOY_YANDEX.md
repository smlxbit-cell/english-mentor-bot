# Деплой на Yandex Cloud (бот 24/7)

Цель: бот работает **без вашего компьютера**. GitHub хранит код, **виртуальная машина (ВМ)** запускает `runbot`.

---

## Сколько стоит

| Сервис | Зачем | Ориентир |
|--------|--------|----------|
| **Compute Cloud (ВМ)** | `runbot` + cron | ~600–1200 ₽/мес (2 GB RAM) |
| **SpeechKit** | голос (STT) | pay-as-you-go, копейки на старте |
| **GitHub** | код | бесплатно |

**~500 ₽** — возможно на минимальной ВМ (1 vCPU, 1 GB), но **лучше 2 GB RAM** (~800 ₽): Django + ffmpeg для Spirit.

SpeechKit и Cloud — **один аккаунт Yandex**, но **разные счета** в консоли.

---

## Что нужно до старта

- [x] Репозиторий: `github.com/smlxbit-cell/english-mentor-bot`
- [ ] Баланс Yandex Cloud (привязать карту)
- [ ] Файл `.env` с ПК (токены)
- [ ] Папка `media/spirit/` с эмоциями (не в Git)

---

## Шаг 1 — ВМ в Yandex Cloud

1. [console.cloud.yandex.ru](https://console.cloud.yandex.ru) → **Compute Cloud** → **Виртуальные машины** → **Создать ВМ**.

2. Параметры (минимум для продакшена):
   - **ОС:** Ubuntu 22.04 LTS
   - **Платформа:** Intel Ice Lake
   - **vCPU:** 2 · **RAM:** 2 GB · **Диск:** 15–20 GB SSD
   - **Публичный IP:** да (автоматически)

3. **SSH-ключ:**
   - На Windows в PowerShell:
     ```powershell
     ssh-keygen -t ed25519 -C "mentor-bot"
     ```
   - Откройте `C:\Users\ВАШ_ЛОГИН\.ssh\id_ed25519.pub`, скопируйте в поле ключа в Yandex.

4. Создайте ВМ. Запишите **публичный IP** (например `51.250.x.x`).

5. **Группы безопасности:** исходящий трафик в интернет разрешён (по умолчанию). Входящий SSH (22) — с вашего IP или 0.0.0.0/0 на время настройки.

---

## Шаг 2 — Подключиться по SSH

```powershell
ssh ubuntu@51.250.x.x
```

(или `yc-user` — смотрите подсказку Yandex при создании ВМ)

---

## Шаг 3 — Установка на сервере

```bash
sudo apt update && sudo apt install -y git
sudo git clone https://github.com/smlxbit-cell/english-mentor-bot.git /tmp/english-mentor-bot
sudo bash /tmp/english-mentor-bot/deploy/server_setup.sh
```

Скрипт создаёт пользователя `mentor`, клонирует репо в `/home/mentor/english-mentor-bot`, ставит Python-зависимости.

---

## Шаг 4 — Скопировать секреты и медиа с ПК

**На вашем Windows** (новое окно PowerShell):

```powershell
# .env (токены — НЕ в GitHub!)
scp C:\english-mentor-bot\.env ubuntu@51.250.x.x:/tmp/.env

# Spirit-видео
scp -r C:\english-mentor-bot\media\spirit ubuntu@51.250.x.x:/tmp/spirit
```

**На сервере:**

```bash
sudo mv /tmp/.env /home/mentor/english-mentor-bot/.env
sudo mkdir -p /home/mentor/english-mentor-bot/media
sudo mv /tmp/spirit /home/mentor/english-mentor-bot/media/spirit
sudo chown -R mentor:mentor /home/mentor/english-mentor-bot
```

В `.env` на сервере добавьте/проверьте:

```env
DEBUG=false
DJANGO_SECRET_KEY=длинная-случайная-строка-50-символов
TIME_ZONE=Europe/Moscow
TELEGRAM_BOT_TOKEN=...
YANDEX_SPEECHKIT_API_KEY=...
YANDEX_FOLDER_ID=...
STT_PROVIDER=yandex
PAYMENT_MODE=mock
```

Сгенерировать секрет (на сервере):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Шаг 5 — База и Spirit

```bash
sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && .venv/bin/python manage.py migrate'
sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && .venv/bin/python manage.py seed_content'
sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && .venv/bin/python manage.py sync_spirit_media --force'
sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && .venv/bin/python manage.py spirit_status'
```

---

## Шаг 6 — Бот как служба (автозапуск)

```bash
sudo cp /home/mentor/english-mentor-bot/deploy/english-mentor-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable english-mentor-bot
sudo systemctl start english-mentor-bot
sudo systemctl status english-mentor-bot
```

Логи:

```bash
sudo journalctl -u english-mentor-bot -f
```

**Важно:** остановите `runbot` на ПК — один токен = один активный polling. Два процесса = конфликт.

---

## Шаг 7 — Напоминания (cron)

```bash
sudo crontab -u mentor -e
```

Вставьте содержимое файла `deploy/cron.example` из репозитория.

---

## Шаг 8 — Проверка

1. Telegram → `/start` — бот отвечает.
2. На сервере: `systemctl status english-mentor-bot` → `active (running)`.
3. Выключите ПК — бот **должен** продолжать работать.

---

## Обновление после правок в Cursor

**На ПК:**

```powershell
git add .
git commit -m "описание"
git push
```

**На сервере:**

```bash
sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && git pull && .venv/bin/pip install -r requirements.txt && .venv/bin/python manage.py migrate'
sudo systemctl restart english-mentor-bot
```

---

## Оплата и ИП (позже)

| Этап | Действие |
|------|----------|
| Сейчас | `PAYMENT_MODE=mock` — тест подписки без денег |
| Модерация | YooKassa + токен в `TELEGRAM_PAYMENT_PROVIDER_TOKEN` |
| Прод | `PAYMENT_MODE=live` в `.env` на сервере + restart |

Тарификация в коде уже есть (390 ₽ / 30 дней).

---

## Частые проблемы

| Проблема | Решение |
|----------|---------|
| Бот молчит | `journalctl -u english-mentor-bot -f` |
| Два бота | остановить `runbot` на ПК |
| Нет Spirit | `sync_spirit_media --force` на сервере |
| Голос не работает | проверить `YANDEX_*` в `.env` |
| **`curl api.telegram.org` timeout** | **Yandex VM не видит Telegram** — см. ниже |

### Telegram заблокирован с VPS (ваш случай)

Проверка на сервере:

```bash
curl -I --max-time 20 https://api.telegram.org
```

Если **timeout** — бот с этого сервера **не сможет** работать без прокси.

**Варианты:**

1. **Проще всего:** другой VPS, где Telegram открыт (Hetzner Финляндия ~€4, Timeweb/Selectel — проверить `curl` перед оплатой).
2. **Остаться на Yandex:** прокси в `.env`:
   ```env
   TELEGRAM_PROXY=socks5://127.0.0.1:1080
   ```
   Поднять SOCKS на маленьком EU-VPS или через `ssh -D` туннель (autossh).
3. После смены хоста или прокси: `systemctl restart english-mentor-bot`.

---

## Схема

```
Вы (Cursor) → git push → GitHub
                              ↓ git pull
                         Yandex Cloud VM
                         ├── runbot (systemd)
                         ├── cron reminders
                         ├── SQLite (позже Postgres)
                         └── .env + media/spirit
                              ↓
                         Telegram пользователи
```
