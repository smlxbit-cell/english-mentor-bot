# Program Structure — English Mentor Bot

**Last updated:** 2026-07-07  
**Purpose:** How the learning program is organized — series, levels, daily flow, rules, exercises.

> **Locked rules (TTS, STT, tutor):** [`PRODUCT_INVARIANTS.md`](PRODUCT_INVARIANTS.md)  
> **Daily program v2 (in progress):** [`DAILY_PROGRAM_V2.md`](DAILY_PROGRAM_V2.md)

---

## 1. Core idea

| Principle | Decision |
|-----------|----------|
| Plot | **One serial for everyone** (Emma, London → Manchester → …) |
| Personalization | **Exercises + word choice + sphere**, not a different story |
| Level | From diagnostic → drives **rules**, **exercise difficulty**, **vocab** |
| Daily unit | **One chapter** = episode + fact + practice woven together |
| Language | **Bilingual**: every EN phrase has RU; all EN is **voicable** 🔊 |

---

## 2. Layers of content

```
┌─────────────────────────────────────────────────────────┐
│  SERIAL (content_app)                                     │
│  Same story episodes for all users                        │
│  curriculum.py → Lesson + LessonStep                      │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  LEVEL VARIANTS (per step, same plot beat)              │
│  A1: simpler MC, shorter speaking targets                 │
│  A2: matching, dialogue, writing                        │
│  B1/B2: harder gaps, longer production                  │
│  → content JSON: level_variants OR separate step sets   │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  AI PERSONALIZATION (runtime)                             │
│  Sphere / interests → personalized exercise bank          │
│  ai_app/services/personalize.py                           │
└─────────────────────────────────────────────────────────┘
```

**Phase 1 (now):** one step list per lesson; level = lesson's `level` field.  
**Phase 2:** `level_variants` on exercises inside the same episode.

---

## 3. Daily chapter (not a weak checklist)

The home screen **«📚 Учиться»** is a **chapter of the adventure**, not a menu of unrelated tasks.

### Inside one day

1. **Hook** — fact of the day (RU + EN, 🔊)
2. **Episode** — main serial scene (~8–15 min)
   - story → vocab (EN/RU + 🔊) → **rule** (table + 🔊) → **many exercises** → speaking → reward → cliffhanger
3. **Words** — SRS repeat (only if due)
4. **Rules drill** — quick practice (only rules **of user's level** not yet ✅)

The **episode is the spine**; fact/words/rules orbit it.

### Episode step template (target)

| # | Step type | Purpose |
|---|-----------|---------|
| 1 | `hook` | Stakes in Russian |
| 2 | `story` | Scene with character |
| 3 | `vocabulary` | 4–6 words: en, ru, example, example_ru, 🔊 |
| 4 | `grammar_note` | Rule table + ✅/👌 + 🔊 examples + 💬 ask |
| 5–10 | `exercise` | MC, fill_gap, matching, word_order, true_false |
| 11 | `speaking` | Voice (Yandex STT) |
| 12 | `ai_dialogue` | Optional character chat |
| 13 | `reflection` | Fact or psychology tip |
| 14 | `reward` | XP |
| 15 | `cliffhanger` | Next episode tease |

**During any content step:** **💬 Спросить** → tutor with voice, **↩️ Вернуться к уроку**.

---

## 4. Exercise types (engine support)

| Type | Status | Use |
|------|--------|-----|
| `multiple_choice` | ✅ | Pick correct phrase |
| `fill_gap` | ✅ | Missing word |
| `word_order` | ✅ | Build sentence |
| `true_false` | ✅ | Quick check |
| `matching` | ✅ checker | Pair question ↔ answer |
| `translation_ru_en` | ✅ | Keywords check |
| `writing` | ✅ + AI | Short production |
| `speaking` | ✅ + STT | Voice target phrase |
| `ai_dialogue` | ✅ | Role-play |

**Fill the bank:** 3–5 exercises per episode minimum; add `matching` to Ep.1–2 in next content pass.

---

## 5. Rules library (A1–B2 map)

### Organization

```
Level (A1 | A2 | B1 | B2)
  └── Topic (Просьбы | Навигация | Глаголы | Вопросы | …)
        └── GrammarRule (key, table, examples, tip_ru)
              └── UserRule (learned | known)
```

### Rules

- User at **A2** sees **only A2 rules** in map and drill (not A1).
- Rules **unlock in episodes** via `grammar_note` + `rule_key`.
- In lesson: **✅ Выучил** / **👌 Уже знаю** → personal library.
- Table UI: **card rows** (not monospace) + **🔊 Слушать примеры**.

### Seeding rules

1. Author in `content_app/grammar_rules.py` or admin `GrammarRule`
2. `python manage.py seed_content` (harvests from curriculum)
3. Link lessons with `rule_key` in `grammar_note` steps

### Topics to fill (backlog)

| Level | Topics to author |
|-------|------------------|
| A1 | Просьбы, Приветствия, Числа, Еда |
| A2 | Вопросы, Present Simple, Места, Small talk |
| B1 | Past Simple, Future, Модальные, Работа |
| B2 | Perfect, Условные, Стили речи, Деловой email |

---

## 6. How to fill the database now (practical order)

1. **Serial Ep.1–2** — enrich in `curriculum.py` (more exercises, matching).
2. **GrammarRule rows** — seed A1/A2 rules referenced in episodes.
3. **Ep.3** — Manchester hotel (A2) + new rule + 5 exercises.
4. **Daily facts** — expand `study_app/daily_facts.py`.
5. **Exercise bank** — `content_app/exercise_bank.py` (optional) for AI fallback.
6. **Level variants** — same episode id, filter steps by `min_level` in JSON.

---

## 7. What changed today (2026-07-05)

- Grammar tables → **readable card layout** (mobile-friendly).
- **🔊 Слушать примеры** on rules (all EN from table + examples).
- Rules map / drill → **only current CEFR level**.
- **💬 Спросить** during lesson → tutor + voice + return to lesson.
- Daily plan framed as **«Глава дня»** (adventure chapter).
- Daily plan UX: one **▶️ Продолжить** CTA, bonus words after episode, rules only in **📖 Правила** (not checklist).

---

## 8. Next content session (recommended)

1. ~~Rewrite Ep.1~~ ✅ Done 2026-07-05
2. ~~Rules bank A1/A2~~ ✅ 16 rules (`rules_bank.py`)
3. ~~Ep.3 Hotel Check-in~~ ✅ Manchester, James, 16 steps
4. ~~Polish daily plan UX~~ ✅ adventure chapter, bonus words after episode, rules → 📖 Правила
5. Ep.4 — First day at work

---

## 9. Daily program v2 — implementation track

**Spec:** [`DAILY_PROGRAM_V2.md`](DAILY_PROGRAM_V2.md)

| Phase | Scope | Status |
|-------|--------|--------|
| **1** | Weighted progress bar, interactive warmup quiz | 🔜 next |
| **2** | Onboarding 20/30/60 min, days/week, rest Sunday; plan sizing in `daily_plan.py` | 🔜 with Phase 1 |
| **3** | Roadmap screen — realistic timeline to next CEFR | planned |
| **4** | Listening blocks, level variants, rule drill bank | ongoing content |

**Today vs target**

| Today | v2 target |
|-------|-----------|
| `daily_minutes` default 10, unused | 20/30/60 drives block list |
| Warmup = read fact/phrase | Warmup = micro-quiz + 🔊 |
| Progress `●●○○○○ 1/2` | `58% · ~22/30 мин` weighted bar |
| Interest hint in greeting only | Interests + sphere shape block mix & AI personalize |
| No roadmap ETA | «~8–12 weeks to B1» map (Phase 3) |
