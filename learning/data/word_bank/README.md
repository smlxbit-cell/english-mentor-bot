# Word bank data import

Drop files here to extend the reference dictionary. Then run:

```bash
python manage.py seed_word_bank
```

## Supported formats

### JSON array

```json
[
  {
    "english": "hello",
    "translation": "привет",
    "cefr_level": "a1",
    "example": "Hello!",
    "example_ru": "Привет!",
    "part_of_speech": "interj",
    "topics": ["greetings"]
  }
]
```

Or `{"words": [ ... ]}`.

### CSV columns

`english`, `translation`, `cefr_level` (required); optional: `example`, `example_ru`, `part_of_speech`, `topics` (comma-separated).

## Built-in sources (always merged)

1. `learning/data/word_bank/remote.json` — ~3600 lemmas (Kelly CEFR + EN↔RU, cached offline)
2. `learning/word_bank/seed_words.py` — curated A1–C1 with examples
3. Vocabulary steps from `content_app/curriculum.py`

Refresh remote cache online (also downloads FreeDict for richer multi-sense RU):

```bash
python manage.py seed_word_bank --fetch --include-remote
```

Manual translation fixes for polysemous words: `learning/data/word_bank/translation_overrides.json`.

Later rows override earlier ones when the same English slug matches.

## Full dictionary later

When you have a licensed EN↔RU dictionary export, convert it to CSV/JSON in the format above and place files in this folder. Re-run `seed_word_bank` — idempotent by `slug`.

Suggested external CEFR word lists (English-only, need RU column added):

- [Kelly Project frequency list](https://github.com/kotoshu/frequency-list-kelly) — CEFR tags, ~7500 lemmas
- [CEFR-J vocabulary profile](https://github.com/openlanguageprofiles/olp-en-cefrj) — CSV with levels

Our bot requires **Russian translation** on every row; skip or fill RU before import.
