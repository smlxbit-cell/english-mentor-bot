# Word bank (Слова)

Reference dictionary for **🎯 Тренировка → Слова**.

## Architecture

| Layer | Model | Role |
|-------|--------|------|
| **Bank** | `WordBankEntry` | Global A1–C1 corpus (EN+RU, examples, CEFR) |
| **Mark** | `UserWordBankStatus` | User marks: know / learning / skip |
| **Personal + SRS** | `Word` + `UserWordProgress` | Training queue, spaced repetition |

Flow:
1. **Hub** — all levels A1–C1 vs CEFR targets (500 / 1k / 2k / 4k / 8k), user level marked
2. **Учить новое** — 10 new, survey, bank, search, level pages
3. **Повтор** — SRS + my dictionary
4. **Разметка** — card flow: Знаю · Учу · Позже → `UserWordBankStatus`

Integration with lessons/tutor: **`docs/WORD_BANK_INTEGRATION.md`**
Navigation map: **`docs/WORD_BANK_NAV.md`**

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

**🎯 Тренировка → Слова** — hub: all level bars + **2 buttons** (Учить новое / Повтор).

Full button map: **`docs/WORD_BANK_NAV.md`**. Do not remove flows without approval.

## Phase 3 (later)

- «Добавить слово» button in lessons
- Topic navigation inside bank
- Licensed full dictionary CSV import

See `learning/data/word_bank/README.md`.
