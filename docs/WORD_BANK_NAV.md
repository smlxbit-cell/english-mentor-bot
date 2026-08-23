# Words section — navigation (locked)

**Entry:** 🎯 Тренировка → Слова → `words:hub`

## Screen 1 — Hub

**Two scenarios (user-facing):**

| Button | Callback | Meaning |
|--------|----------|---------|
| 🎯 Тренировка · N | `words:repeat` | Practice words you marked «учу» |
| 📘 Новые слова | `words:new` | Add new words to your list |

## Screen 2 — 📘 Новые слова

| Button | Action |
|--------|--------|
| Начать · 10 | 10 random **unlearned** words at your level → 🔊 lesson → training |
| 📖 Выбрать в словаре | Browse dictionary, mark знаю / учу |
| ← Слова | Hub |

## Screen 2b — 📖 Выбрать в словаре

| Button | Action |
|--------|--------|
| 👀 Что знаешь? | Quick survey 10 words |
| 📁 Темы / 📊 Уровни | Dictionary browse — **tap word** → Знаю / Учу |
| 🔍 Поиск | Search |
| ← Новые слова | Screen 2 |

Marked «учу» → **🎯 Тренировка** on hub.

## Screen 3 — 🎯 Тренировка

| Button | Action |
|--------|--------|
| 🎯 Начать · N | SRS training session |
| 📗 Мои слова | Your lists (учу / знаю / выучил) |
| ← Слова | Hub |

## Lesson flow (Начать · 10)

- During lesson: **← Выход** (not back to «новые слова»)
- After lesson: **🎯 Тренировка · N** or **← Слова**

Internal code may still use `words:repeat`, `words:bank` — UI never says «банк» or «повтор».
