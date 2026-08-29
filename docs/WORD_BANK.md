# Word bank (Слова)

Reference dictionary for **🎯 Тренировка → Слова**.

## Locked product map

**`docs/WORD_BANK_NAV.md`** — canonical navigation, button order, training scope, queue policy (min 10, no spam), post-drill review.  
**Read before any change** to handlers/keyboards/service for words. Owner-approved 2026-08-25.

Summary invariants: **`docs/PRODUCT_INVARIANTS.md` §8**.

## Architecture

| Layer | Model | Role |
|-------|--------|------|
| **Bank** | `WordBankEntry` | Global A1–C1 corpus (EN+RU, examples, CEFR) |
| **Mark** | `UserWordBankStatus` | User marks: know / learning / skip |
| **Personal + SRS** | `Word` + `UserWordProgress` | Training queue, spaced repetition |

Flow:
1. **Hub** — level progress vs CEFR targets; **🎯 Тренировка** pulls from «Учить» pile (up to 10)
2. **📘 Новые слова** — compact entry: Уровни / Знаю? / Поиск (see NAV doc)
3. **📖 Словарь** — browse by level; page-scoped training + survey + bulk mark
4. **Drill** — multi-step training + **final Знаю/Учить pass** after completion
5. **Queue policy** — auto top-up to 10 only when pile &lt; 10; no daily dump if user has 79+

Integration with lessons/tutor: **`docs/WORD_BANK_INTEGRATION.md`**

## Service constants

| Constant | Value | Meaning |
|----------|-------|---------|
| `DAILY_NEW_WORDS` | 10 | Words per training session / daily slice |
| `MIN_LEARNING_QUEUE` | 10 | Auto top-up threshold for «Учить» pile |

Key functions: `ensure_min_learning_queue`, `pick_training_words`, `get_review_words_for_dicts`.

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

**🎯 Тренировка → Слова** — hub + dictionary paths per **`docs/WORD_BANK_NAV.md`**. Do not remove flows without approval.

## Phase 3 (later)

- «Добавить слово» button in lessons
- Topic navigation inside bank
- Licensed full dictionary CSV import

See `learning/data/word_bank/README.md`.
