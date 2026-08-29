# Чеклист правил грамматики — мастер-трекер

**Цель:** 422 правила · A1→C1 · не потерять ни одно.  
**Сyllabus:** `GRAMMAR_RULES_ROADMAP.md` · **UX:** `GRAMMAR_NAV.md`

## Прогресс (обновлять при каждой загрузке)

| | Текст в банке | 🖼 Spirit | Осталось |
|---|:---:|:---:|:---:|
| **A1** | 33 / 70 | 34 / 70 | 36 |
| **A2** | 10 / 90 | 0 / 90 | 80 |
| **B1** | 3 / 92 | 0 / 92 | 89 |
| **B2** | 1 / 94 | 0 / 94 | 93 |
| **C1** | 0 / 76 | 0 / 76 | 76 |
| **ИТОГО** | **50 / 422** | **34 / 422** | **366** |

**Фаза 1 (сейчас):** текст + картинка на каждый key.  
**Фаза 2 (потом):** тренировка, intro, дневной план.

**Очередь генерации:** A1 ⚡ глаголы ✅ → **A1 👋 фразы** → 📝 слова → 🔗 связки → 🧩 синтаксис.

---

## A1 — полный список (70)

Формат: `key` · раздел · текст · 🖼

### 👋 Фразы (14)

| key | title | T | 🖼 |
|-----|-------|:-:|:-:|
| greetings-hello | Hello / Hi / Good morning | ✅ | ✅ |
| greetings-goodbye | Goodbye / See you | ✅ | ✅ |
| polite-requests | I would like… / please | ✅ | ✅ |
| thank-you-responses | Thank you / You're welcome | ✅ | ✅ |
| sorry-excuse-me | Sorry / Excuse me | ✅ | ✅ |
| yes-no-ok | Yes / No / OK | ✅ | ✅ |
| introducing-yourself | My name is… | ✅ | ✅ |
| numbers-1-20 | Numbers 1–20 | ✅ | ✅ |
| numbers-21-100 | 21–100 | ✅ | ✅ |
| time-oclock | What time is it? | ✅ | ✅ |
| days-months | Days / months | ✅ | ✅ |
| cafe-order-basic | A coffee, please | ✅ | ✅ |
| how-are-you | How are you? | ✅ | ✅ |
| good-night | Good night | ✅ | ✅ |

### ⚡ Глаголы (18)

| key | title | T | 🖼 |
|-----|-------|:-:|:-:|
| to-be-basics | I am / you are / he is | ✅ | ✅ |
| to-be-negative | am not / isn't / aren't | ✅ | ✅ |
| to-be-questions | Am I…? / Are you…? | ✅ | ✅ |
| to-be-short-forms | I'm / you're / he's | ✅ | ✅ |
| there-is-are-affirm | There is / There are | ✅ | ✅ |
| there-is-are-questions | Is there…? | ✅ | ✅ |
| have-got-affirm | I have / She has | ✅ | ✅ |
| have-got-questions | Do you have…? | ✅ | ✅ |
| imperatives-affirm | Open… / Sit down / Listen | ✅ | ✅ |
| imperatives-negative | Don't… / Don't worry | ✅ | ✅ |
| can-ability | I can / She can | ✅ | ✅ |
| can-permission | Can I…? / Can you…? | ✅ | ✅ |
| can-negative | I can't / She can't | ✅ | ✅ |
| present-simple-i-you | I work / You live | ✅ | ✅ |
| present-simple-he-s | He works (+s) | ✅ | ✅ |
| like-love-ing | I like reading | ✅ | ✅ |
| want-would-like | want / would like | ✅ | ✅ |
| lets | Let's go | ✅ | ✅ |

### 📝 Слова (16) · 🔗 Связки (10) · 🧩 Синтаксис (12)

→ полные keys в `GRAMMAR_RULES_ROADMAP.md` § A1 (строки 93–140).

---

## A2 — 90 правил (keys в roadmap + существующие)

**✅ текст:** present-simple-affirmative, present-simple-questions, wh-questions-basics, navigation-where, navigation-directions, prepositions-place, modal-can, modal-could-polite, hotel-check-in, work-small-talk

**⬜ блоки:** Present Continuous (3), Past Simple reg/irreg (6), going to (3), must/should (4), comparatives (4), … — см. roadmap § A2

---

## B1 — 92 · B2 — 94 · C1 — 76

Полная структура по 5 разделам — `GRAMMAR_RULES_ROADMAP.md` § B1–C1.  
Keys дописываем в checklist по мере старта уровня (после A1=100%).

---

## Файлы на сервере

```
media/spirit/rules/{key}.jpg   ← картинка
content_app/rules_bank.py      ← текст
```

После каждой пары: `seed_content` на проде.
