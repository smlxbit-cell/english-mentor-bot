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
- **▶️ Учить 10 новых** — daily batch from unseen bank words
- **🔄 Повторить** — SRS due queue
- **✅ Разметить знания** — know/learn/skip survey
- **A1…C1** — level detail + scale
- **🗂 Мой словарь** — personal list from lessons + marked words

## Phase 3 (later)

- «Добавить слово» button in lessons
- Topic navigation inside bank
- Licensed full dictionary CSV import

See `learning/data/word_bank/README.md`.
