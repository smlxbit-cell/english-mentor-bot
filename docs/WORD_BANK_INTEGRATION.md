# Words ↔ rest of the bot (integration plan)

**Status:** partial today · full link with daily plan = final stage (agreed).

## Single vocabulary model

| Layer | Model | Role |
|-------|--------|------|
| Bank | `WordBankEntry` | Global A1–C1 corpus |
| Mark | `UserWordBankStatus` | know / learning / skip (statistics by level) |
| Personal + SRS | `Word` + `UserWordProgress` | Training queue, spaced repetition |

Any “add word” action in the bot should eventually update **both** mark (stats) and personal SRS when the user chooses «Учу».

## Today (implemented)

- **Lessons:** `save_lesson_words()` after episode → `UserWordProgress` (SRS queue).
- **Words hub:** survey, bank, daily 10, repeat, my dictionary.
- **Survey / bank card:** `mark_bank_entry()` → `UserWordBankStatus` + sync to `Word` when «Учу».

## Next (do not ship daily-plan tie until owner approves)

### Daily plan ↔ words

1. Daily chapter includes **10 words at user level** (from bank or lesson vocab).
2. In lesson OR plan step: **Знаю** / **Учу** on each word.
3. «Учу» → `UserWordProgress` + `UserWordBankStatus.LEARNING`.
4. «Знаю» → `UserWordBankStatus.KNOWN` (counts toward level bar).
5. Same words visible in **🎯 Тренировка → Слова** without re-entry.

### Rules training

- Optional **«Добавить слово»** on unknown word in rule drill (lookup bank → mark).

### Tutor

- **«В словарь»** on highlighted English in tutor reply (match `WordBankEntry` or create `Word`).

### Lesson vocabulary

- When lesson word matches bank slug: also write `UserWordBankStatus` so level progress updates.

## Hub UX (locked 2026-08-23)

- **Screen 1:** level bars A1–C1 (target = CEFR goal), user level marked, **2 buttons**.
- **Учить новое:** 10 new, survey, bank, search, level drill-down.
- **Повтор:** SRS, my dictionary.

Do not remove flows from sub-menus without explicit approval.
