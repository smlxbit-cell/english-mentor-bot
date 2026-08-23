# Words section — navigation (locked)

**Entry:** 🎯 Тренировка → Слова → `words:hub`

## Screen 1 — Hub

**Text:**
- Title + **твой уровень** (from diagnostic)
- Progress **A1 … C1** — `знаю / CEFR-цель · учу` (targets: 500 / 1k / 2k / 4k / 8k)
- Current level marked `← ты здесь`
- No extra counters under bars (no «не проверено» line)

**Buttons (2 only):**

| Button | Callback | Opens |
|--------|----------|--------|
| Учить новое | `words:new` | Screen 2 |
| Повтор · N | `words:repeat` | Screen 3 |

## Screen 2 — Учить новое

| Button | Action |
|--------|--------|
| Начать · 10 | Урок: 1 слово → 🔊 → «Дальше» ×10 → тренировка |
| В словарь | Screen 2b (добавить слова без урока) |
| ← Слова | Hub |

**Важно:** слова попадают в «учу» только после прохождения урока и нажатия «Тренировка». «Знаю ✅» в уроке — сразу в статистику.

## Screen 2b — В словарь

| Button | Action |
|--------|--------|
| 👀 Что знаешь? | Level picker → survey 10 words |
| 📖 Словарь | Browse corpus by level/topic |
| 🔍 Поиск | Text search |
| ← Учить новое | Screen 2 |

Не урок — только отметить слова в свой список (знаю / учу / позже).

## Screen 2c — Что знаешь? (levels)

Tip: start with ★ user level. Pick A1–C1 → 10 cards (Знаю / Учу / Позже).

## Screen 3 — Повтор

| Button | Action |
|--------|--------|
| 🔄 Повтор · N | SRS session (if due) |
| 📗 Мой словарь | Personal word lists |
| ← Слова | Back to hub |

**Text:** «В учёбе · к повторению» — counts only here, not in Мой словарь.

## Screen 3b — Мой словарь

| Button | Action |
|--------|--------|
| 📗 Учу / ✅ Знаю / 🌟 Выучил | Filter personal lists |
| 📁 Темы / 📊 Уровни | Browse by topic or CEFR |
| ← Повтор | Back to Screen 3 |

No 🔄 Повтор button here (repeat lives on Screen 3 only).

## Topics in corpus

Remote Kelly words are auto-tagged by topic (not dumped into «Общие»). Run `classify_word_topics` after seed to refresh existing DB rows.

## Integration roadmap

See **`docs/WORD_BANK_INTEGRATION.md`** (lessons, tutor, rules).

Legacy: `words:add` → hub.
