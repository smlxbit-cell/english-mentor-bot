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
| Учить · 10 | Daily intro + quiz (`words:learn:daily`) |
| Выбрать слова | Screen 2b |
| ← Слова | Hub |

## Screen 2b — Выбрать слова

| Button | Action |
|--------|--------|
| 👀 Что знаешь? | Level picker → survey 10 words |
| 📖 Словарь | Browse corpus by level/topic |
| 🔍 Поиск | Text search |
| ← Учить новое | Screen 2 |

## Screen 2c — Что знаешь? (levels)

Tip: start with ★ user level. Pick A1–C1 → 10 cards (Знаю / Учу / Позже).

## Screen 3 — Повтор

| Button | Action |
|--------|--------|
| 🔄 Повтор · N | SRS session (if due) |
| 📗 Мой словарь | Учу / Знаю / Выучил / темы |
| ← Слова | Back to hub |

## Integration roadmap

See **`docs/WORD_BANK_INTEGRATION.md`** (lessons, tutor, rules).

Legacy: `words:add` → hub.
