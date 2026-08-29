# Как мы разрабатываем English Mentor Bot

Короткая памятка: где код, как синхронизировать ПК / телефон / сервер.

**Обновлено:** 2026-08-22

---

## 1. Три места — одна правда

| Место | Путь / URL | Роль |
|-------|------------|------|
| **ПК (главная папка)** | `C:\english-mentor-bot` | Здесь Cursor редактирует код |
| **GitHub (облако)** | https://github.com/smlxbit-cell/english-mentor-bot | Бэкап + история + синхронизация |
| **Сервер (бот 24/7)** | `109.71.244.197` → `/home/mentor/english-mentor-bot` | Telegram-бот для пользователей |

```text
ПК (Cursor)  ──git push──►  GitHub  ──git pull──►  Сервер
     ▲                            │
     └──────── git pull ──────────┘   (телефон / второй ПК)
```

**Правило:** работаем в **одной** папке на ПК — `C:\english-mentor-bot`.  
Не путать с «English learning bot project» (старая копия — можно удалить).

---

## 2. Что делает агент в Cursor

После задачи агент обычно:

1. Меняет файлы в `C:\english-mentor-bot`
2. `git commit` + `git push` на GitHub (`main`)
3. (по запросу) деплой на сервер: `git pull` + `seed_content` + `restart`

**Вам не нужно** нажимать «Create Branch & Commit», если агент уже закоммитил и написал «запушено».

---

## 3. Вкладка «Changes» / «Create Branch & Commit»

| Ситуация | Что делать |
|----------|------------|
| Агент написал «запушено на GitHub» | **Ничего** — всё уже в облаке |
| Видите «Unstaged» / 10 files changed | Либо попросите агента: *«закоммить и запушь»*, либо сами: Commit → Push |
| «Create Branch & Commit» | Нужно только если **вы** коммитите вручную. Обычно работаем в **`main`**, без новых веток |

**Не создавайте** ветку `restore/local-progress` и репозиторий `Mariaa33/...` — рабочий репозиторий только **`smlxbit-cell/english-mentor-bot`**.

---

## 4. Телефон (Cursor на телефоне)

| Можно | Нельзя / сложно |
|-------|------------------|
| Чат с агентом, мелкие правки | Полноценный деплoy без SSH |
| `git pull` (если настроен Git) | Локальный `runbot` (конфликт с сервером) |
| Тест бота в **Telegram** | Секреты `.env` — только с ПК |

**Открывать на телефоне:** проект **English mentor bot development** → `git pull origin main` перед работой.

Код на телефоне **не заменяет** папку на ПК — оба тянут одно и то же с GitHub.

---

## 5. Обновить версию на ПК (после push с другого места)

```powershell
cd C:\english-mentor-bot
git pull origin main
```

---

## 6. Деплой на сервер (бот для пользователей)

Только после push на GitHub:

```powershell
ssh root@109.71.244.197 "sudo -u mentor bash -c 'cd /home/mentor/english-mentor-bot && git pull && .venv/bin/python manage.py seed_content' && systemctl restart english-mentor-bot"
```

Если менялся только код (не curriculum) — можно без `seed_content`.

**Не запускайте** на ПК: `python manage.py runbot` — пока сервер работает, будет конфликт.

---

## 7. Секреты

- `.env` — **только на ПК и сервере**, не в GitHub
- При новом ПК: скопировать `.env` вручную или из `.env.example`

---

## 8. Полезные документы в репозитории

| Файл | Зачем |
|------|--------|
| `PROJECT_STATE.md` | Что за проект, архитектура |
| `docs/WORD_BANK_NAV.md` | **LOCKED:** Слова / словарь / тренировка — навигация и логика очереди |
| `docs/PRODUCT_INVARIANTS.md` | Не ломать TTS, STT, тьютора, словарь (§8) |
| `docs/TARIFFS.md` | Тарифы и лимиты |
| `docs/YOOKASSA_SUBMISSION.md` | Материалы для ЮKassa |
| `docs/DAILY_PROGRAM_V2.md` | План дня |

---

## 9. Чеклист «всё синхронизировано»

- [ ] `git status` на ПК — clean (нет незакоммиченных файлов)
- [ ] На GitHub виден последний commit
- [ ] На сервере `git log -1` совпадает с GitHub
- [ ] В Telegram бот отвечает после деплоя

---

## 10. Команды для владельца

```powershell
# Где я?
cd C:\english-mentor-bot
git status
git log -1 --oneline

# Кто платил (на сервере или локально с БД)
python manage.py list_user_billing
```

Django Admin на сервере: `/admin/` → User profiles (колонки «Тариф», «Подписка до»).
