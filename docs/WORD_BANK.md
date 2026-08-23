# Word bank (Слова)

Reference dictionary for **🎯 Тренировка → Слова**.

## Architecture

| Layer | Model | Role |
|-------|--------|------|
| **Bank** | `WordBankEntry` | Global A1–C1 corpus (EN+RU, examples, CEFR) |
| **Mark** | `UserWordBankStatus` | User marks: know / learning / skip |
| **Personal + SRS** | `Word` + `UserWordProgress` | Training queue, spaced repetition |

Flow:
1. **Hub** — progress bars per level (A1…user level), counters «знаю / учу / осталось»
2. **Разметка** — card flow: ✅ Знаю · 📗 Учить · ⏭️ Пропустить
3. **Учить 10 новых** — intro + RU→EN quiz (SRS)
4. **Повторить** — due words from personal SRS

Lower levels are always checked (A2 user still sees A1 gaps).

## Seed the database

```bash
python manage.py migrate
python manage.py seed_word_bank --include-remote
```

First-time online expand (Kelly CEFR + EN↔RU dictionary, caches `remote.json`):

```bash
python manage.py seed_word_bank --fetch --include-remote
```

Sources (later overrides earlier for same slug):

1. `learning/data/word_bank/remote.json` — ~3600 lemmas (cached download)
2. `learning/word_bank/seed_words.py` — curated examples EN+RU
3. `content_app/curriculum.py` — program vocabulary
4. Extra `learning/data/word_bank/*.json|csv`

## Telegram UX

**🎯 Тренировка → Слова** opens the hub (not empty-state only).

Buttons:
- **▶️ 10 новых** | **🔄 Повтор** — daily batch + SRS
- **👀 Что знаешь?** — quick check: know / learn / later (not «разметка»)
- **🗂 Мой словарь** — groups + 6 words per page (no long canvas)
- **📖 Банк слов** — browse by level/topic, 6 per page
- **🔍 Поиск** — find in bank by EN or RU

## Phase 3 (later)

- «Добавить слово» button in lessons
- Topic navigation inside bank
- Licensed full dictionary CSV import

See `learning/data/word_bank/README.md`.
