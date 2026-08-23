# Words section — navigation (locked)

**Entry:** 🎯 Тренировка → Слова → `words:hub`

## Hub (one screen)

**Text shows:**
- Твой уровень (из теста)
- Progress bars **A1 … user level** (знаю / цель, учу)
- Не проверено · К повторению · Сегодня

**Buttons (4 rows):**

| Row | Buttons | Goes to |
|-----|---------|---------|
| 1 | ▶️ 10 новых · 🔄 Повтор | daily learning · SRS |
| 2 | 👀 Что знаешь? · 📗 Мой словарь | survey cards · personal lists |
| 3 | 📖 Банк слов · 🔍 Поиск | browse bank · text search |
| 4 | A1 A2 B1 B2 C1 | level stats + check + words |

Do **not** remove these flows without explicit product approval.

## Sub-screens

- **👀 Что знаешь?** — 10 cards, Знаю / Учу / Позже → `UserWordBankStatus`
- **📗 Мой словарь** — Учу / Знаю / Выучил / Темы / Уровни (6 слов на страницу)
- **📖 Банк слов** — levels, темы, 6 слов на страницу
- **Level (A1…)** — stats, проверить 10, открыть слова уровня

Legacy callbacks `words:new`, `words:repeat` → redirect to hub.
