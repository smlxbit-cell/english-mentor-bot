# Content Quality Standard

**Last updated:** 2026-07-15  
**Purpose:** Author checklist for episodes, facts, rules, exercises, and tests.  
**Related:** [`PRODUCT_INVARIANTS.md`](PRODUCT_INVARIANTS.md), [`PROGRAM_STRUCTURE.md`](PROGRAM_STRUCTURE.md), [`DAILY_PROGRAM_V2.md`](DAILY_PROGRAM_V2.md)

Use this before shipping any new curriculum step, daily fact, or diagnostic item.

---

## 1. Language & bilingual

| Rule | Detail |
|------|--------|
| Every English phrase | Has a natural Russian translation immediately under it (`🇬🇧` / `(…)` or paired `en`/`ru` fields). |
| No invented words | Prefer common, real vocabulary; if niche, mark and explain. |
| Natural RU | Translate meaning, not word-by-word calques. |
| Level-fit | A1–A2: short sentences. B1–B2: more nuance, still clear. C1: register/nuance OK, still bilingual. |

## 2. TTS (🔊)

| Rule | Detail |
|------|--------|
| Listenability | Every EN fragment in lessons, facts, rules, dictionary, diagnostic must be listenable. |
| Mixed RU+EN | Put EN on its own `🇬🇧` line or set `content.speak_en` / structured `en` fields — do not bury EN only inside RU prose. |
| Examples in rules | Each table EN example and `examples[].en` must voice cleanly. |

## 3. Grammar & rules

| Rule | Detail |
|------|--------|
| Reliable rules only | Use standard CEFR patterns (tables like `GrammarRule` / `rules_bank`). No folklore. |
| Table + tip | Rule steps: Russian explanation + bilingual table + tip. |
| Link exercises | Exercises for a rule set `rule_key` and a short `explanation` / `hint_detail_ru`. |
| Wrong answers | Prefer deep explanations: why correct, why each distractor fails (translations / form notes). |

## 4. Exercises & tests

| Rule | Detail |
|------|--------|
| Variety | In one episode: mix MC, gap, matching, word order, true/false, speaking — avoid 4× same type in a row. |
| Distractors | Plausible mistakes learners make; not nonsense. |
| Explanations | Correct path + “why not others” when options exist. |
| Speaking targets | Clear, speakable target phrase; STT-friendly length. |

## 5. Daily facts & warmups

| Rule | Detail |
|------|--------|
| Verifiable | Short, checkable cultural/language facts — no shady “factoids”. |
| Bilingual | `ru` + `en` both present; EN listenable. |
| Interest tags | Prefer tagging facts (`topics`) so warmup can bias to user interests. |

## 6. Story & personalization

| Rule | Detail |
|------|--------|
| One serial | Same Emma plot for everyone. |
| Personalize practice | Interests / profession / sphere change **exercises and examples**, not the plot. |
| Hook → cliffhanger | Each episode ends with a concrete tease of the next situation. |

## 7. Pre-ship smoke (manual)

1. Episode opens → auto/voice EN on first story or dialogue.  
2. Tap 🔊 on vocab and rule examples.  
3. Fail one exercise → explanation readable in RU.  
4. Speaking step accepts voice or text.  
5. Daily plan for 20 / 30 / 60 min looks different; rest day lighter.

---

**North star:** interesting personal tutor — reliable knowledge, clear practice, strong motivation — not a generic checklist.
