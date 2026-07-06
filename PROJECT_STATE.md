# PROJECT_STATE — English Mentor Bot

> Живой документ. Здесь фиксируется реальное состояние проекта, принятые
> архитектурные решения и план работ. Обновлять по мере продвижения.

## 1. Что это за проект

Django-проект **English Mentor Bot** — обучающий сервис по английскому языку
для русскоязычной аудитории (Россия). **Основной интерфейс — Telegram-бот.**
Веб-часть (Django) остаётся только для админки (наполнение контента) и простого
лендинга.

Главная цель продукта — **не заглушка, а интересный интерактивный тьютор**,
который удерживает мотивацию ученика:

- профессиональная адаптивная **диагностика уровня** (интерактивная, с голосом);
- **интерактивные уроки** с медиа (картинки, аудио, видео, GIF), упражнениями,
  диалогами, историями и персонажами;
- **AI-проверка ответов** (экономно по токенам), подсказки, мини-грамматика;
- **геймификация**: XP, стрики, очки, бонусы, достижения;
- **словарь** с интервальным повторением, прослушиванием слов и контекста;
- 2 бесплатных пробных урока → подписка **390 ₽ / 30 дней** (без автопродления).

Ученик учится маленькими шагами: диагностика → пробные уроки → подписка →
ежедневные сессии, адаптированные под его уровень, интересы и слабые места.

---

## 2. ВАЖНО: проект уже создан

Проект уже существует в `C:\english-mentor-bot`. **Не создавать заново.**

Не предлагать: `startproject`, `startapp` (кроме явно новых app’ов из плана),
`git init`, `.venv`, `.env`, суперпользователя, повторную базовую настройку.

---

## 3. Стек и окружение

- Python + Django 6.0, SQLite (dev).
- `python-telegram-bot==22.8` (async, polling).
- `httpx` (HTTP-клиент для OpenAI и Yandex SpeechKit — уже в зависимостях).
- `python-dotenv`, `pillow`.
- Секреты в `.env` (см. `.env.example`).

### Принятые решения (утверждено пользователем)

| Тема | Решение |
|------|---------|
| Архитектура | Консолидация на «продуктовых» app’ах; `bot_app` (legacy) выводится из эксплуатации |
| AI | **OpenAI** (`gpt-4o-mini`) за абстракцией провайдера (легко заменить) |
| Голос (STT) | **Yandex SpeechKit** за абстракцией |
| Интерфейс | **Telegram-first**; веб = админка + лендинг |
| Тариф | Один план: **390 ₽ / 30 дней**, без автопродления, 2 пробных урока + бесплатная диагностика |
| Оплата | YooKassa; пока `PAYMENT_MODE=mock`, реальная оплата — после модерации магазина |

---

## 4. Текущее состояние кода (реальность на момент рефакторинга)

В репозитории было **три параллельных, несвязанных архитектуры**. Это и есть
то, что «нужно поправить/переписать».

### 4.1. `bot_app` — LEGACY, единственное, что реально работало
- `management/commands/runtelegrambot.py` — рабочий бот: диагностика (5 вопросов,
  проверка точным совпадением строки) → 2 пробных урока (просто текст) → paywall →
  подписка (mock + Telegram/YooKassa invoice).
- Модели: `TelegramUser`, `UserProfile`, `DiagnosticQuestion/Answer`, `Lesson`,
  `Subscription/Plan`, `Payment`.
- В том же `models.py` добавлена большая «adaptive content» схема (`Level`, `Course`,
  `StoryWorld`, `LessonTemplate`, `LessonBlock`, `ExerciseTemplate`, `MediaAsset`…),
  но она **нигде не используется**, не в админке, без сидов. Мёртвый каркас.
- **Судьба:** вывести из эксплуатации. Логику диагностики/уроков/оплаты перенести
  в `telegram_app` поверх «продуктовых» моделей. Модели `bot_app` пометить legacy и
  затем удалить миграцией после переноса данных (данных в проде нет).

### 4.2. Продуктовые app’ы — чистая целевая архитектура (моделей достаточно, связей с ботом нет)
- `users_app`: `UserProfile` (telegram_id, cefr_level, learning_goal, interests,
  onboarding, daily_minutes, preferred_formats) + `Interest`, `UserInterest`.
- `content_app`: `ContentTheme`, `Phrase`, `Character`, `StoryArc`, `StoryEpisode`,
  `MediaAsset`. (Расширяем интерактивными уроками — см. план.)
- `study_app`: `DailySession`, `DailySessionBlock`, `UserAnswer` (runtime, per-user).
- `progress_app`: `UserWordProgress`, `SkillProgress`, `ErrorLog`.
- `gamification_app`: `UserStats`, `Achievement`, `UserAchievement`.
- У всех есть admin + `content_app seed_demo` с демо-данными.
- **`telegram_app` и `ai_app` — пустые заглушки.** Здесь и будет основная работа.

### 4.3. `learning` + `core` — веб
- `learning.Word` + веб-страницы (список/добавление/тренировка слов), лендинг `core`.
- **Судьба:** `learning.Word` — оставить как источник словаря (на него уже ссылается
  `progress_app.UserWordProgress`). Веб-тренажёр оставить как есть; развитие — в боте.

### 4.4. Дубли, которые устраняем
- 3 «профиля пользователя» → единый **`users_app.UserProfile`** (ключ = `telegram_id`).
- 2 `MediaAsset` (bot_app, content_app) → **`content_app.MediaAsset`**.
- 2 `StoryEpisode`/`Character` → **`content_app`**.
- Словарь: `learning.Word` (канон) + `content_app.Phrase` (фразы/контекст).

---

## 5. Целевая архитектура (Telegram-first)

```
users_app        — учётка ученика (telegram_id), уровень, цели, интересы, онбординг
content_app      — АВТОРСКИЙ контент (в админке): темы, фразы, персонажи, истории,
                   медиа + НОВОЕ: Lesson / LessonStep / Exercise / DiagnosticItem
study_app        — RUNTIME: сессии ученика, попытки, ответы, прогресс по урокам
progress_app     — прогресс по словам (SRS), по навыкам, лог ошибок
gamification_app — XP, уровни, стрики, очки/бонусы, достижения
billing_app      — (НОВЫЙ) SubscriptionPlan / Subscription / Payment (YooKassa)
ai_app           — абстракция AI-провайдера (OpenAI), экономная проверка ответов,
                   подсказки, диалоги-партнёр + STT (Yandex SpeechKit)
telegram_app     — САМ БОТ: хендлеры, клавиатуры, сценарии, команда runbot
learning + core  — веб: словарь-тренажёр + лендинг (второстепенно)
bot_app          — LEGACY, выводится из эксплуатации
```

Разделение контента и рантайма:
- **content_app** = шаблоны/материал (что показываем).
- **study_app** = что происходит у конкретного ученика (его сессии/ответы).

---

## 6. План работ (фазы)

### Фаза 0 — Фундамент (без БД-миграций) ✅ в работе
- [x] Аудит проекта, фиксация решений (этот документ).
- [x] `docs/PRODUCT_DESIGN.md` — методическая программа (диагностика, 2 урока,
      геймификация, словарь, экономия AI, авторские права).
- [x] `config/settings.py`: MEDIA, конфиг OpenAI / Yandex / YooKassa, цена 390 ₽.
- [x] `.env.example`.
- [x] `ai_app` сервисный слой: провайдер (OpenAI + mock), экономный чекер, промпты.
- [x] `ai_app` речь: клиент Yandex SpeechKit + заглушка.

### Фаза 1 — Модели и консолидация (КОД ГОТОВ ⏳ ждёт `migrate`)
- [x] `content_app`: `DiagnosticItem`, `Lesson`, `LessonStep` (интерактив в
      `content` JSON; связи с `MediaAsset`, `Character`, `StoryEpisode`).
- [x] `billing_app`: `SubscriptionPlan`, `Subscription`, `Payment`.
- [x] `users_app.UserProfile`: `diagnostic_completed`, `trial_lessons_used`,
      `weak_skills`.
- [x] `study_app`: `LessonProgress`, `StepAttempt`. Admin для всех новых моделей.
- [ ] `makemigrations` + `migrate` (нужен shell — не удалось выполнить в сессии).
- [x] `bot_app` помечен legacy в `INSTALLED_APPS` (пока установлен, удаление позже).

### Фаза 2 — Бот (КОД ГОТОВ ⏳ ждёт запуска)
- [x] `telegram_app`: команда `runbot`, роутер (`on_callback/on_text/on_voice`),
      клавиатуры.
- [x] Адаптивная диагностика (PRODUCT_DESIGN §2), голосовой ответ (Yandex STT).
- [x] Движок интерактивного урока (шаг-за-шагом), отправка медиа.
- [x] AI-проверка открытых заданий (экономно), подсказки, AI-диалог с персонажем.
- [x] Геймификация: XP, стрик, достижения, экран итогов.
- [x] Paywall 390 ₽ (mock), прогресс, словарь.

### Фаза 3 — Контент (КОД ГОТОВ ⏳ ждёт `seed_content`)
- [x] `content_app seed_content`: адаптивная диагностика (9 заданий) + 2
      флагманских урока («Coffee in London», «Meeting on a Plane») + достижения.
- [ ] Демо-медиа (картинки/аудио) — добавляются через админку (upload) или
      `MediaAsset.source_url`.

> ⚠️ Весь код Фаз 1–3 написан, но НЕ проверен запуском: в сессии не работал
> терминал. Первым делом выполнить блок «Как запускать» ниже и починить возможные
> мелочи.

### Фаза 4 — Оплата боевая (после модерации магазина)
- [ ] Подключить реальные ключи YooKassa, переключить `PAYMENT_MODE=live`, тест оплаты.

### Дальнейшее развитие
- Мини-сериал с персонажем (генерация изображений), подкасты, карточки-ситуации,
  озвучка слов (TTS), еженедельные челленджи, реферальные бонусы.

---

## 7. Как запускать (dev)

```bash
python manage.py makemigrations       # сгенерит миграции для новых моделей
python manage.py migrate
python manage.py seed_content         # диагностика + 2 флагманских урока + ачивки
python manage.py seed_demo            # (опц.) доп. демо-контент content_app
python manage.py runbot               # запуск нового Telegram-бота (telegram_app)
```

- Новый бот: `python manage.py runbot` (telegram_app).
- Legacy-бот (старый, примитивный): `python manage.py runtelegrambot` (bot_app) —
  использовать только как fallback, не одновременно с `runbot`.
- AI работает при заданном `OPENAI_API_KEY` (иначе mock). Голос — при
  `YANDEX_SPEECHKIT_API_KEY` (иначе попытка озвучки принимается без оценки).
