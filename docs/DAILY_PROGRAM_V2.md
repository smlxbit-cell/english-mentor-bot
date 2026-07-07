# Daily Program v2 — Specification

**Last updated:** 2026-07-07  
**Status:** Approved direction — **Phase 1 + 2** are the first implementation track.  
**Owner decisions:** product owner (confirmed in chat 2026-07-07).

**Related (read before changing code):**

- [`PRODUCT_CONCEPT.md`](PRODUCT_CONCEPT.md) — north star & serial story
- [`PROGRAM_STRUCTURE.md`](PROGRAM_STRUCTURE.md) — current daily chapter layout
- [`PRODUCT_INVARIANTS.md`](PRODUCT_INVARIANTS.md) — **do not break** voice, TTS, STT, tutor

---

## 0. One sentence

> **Every learner gets a full, interactive, high-quality English program** — sized to their level, interests, and schedule — that feels like a cool personal tutor, not a generic app.

---

## 1. North star (locked)

These goals apply to **all** future work. When we change something, we extend — we do not forget this.

| Pillar | What it means in the product |
|--------|------------------------------|
| **Personal program** | Plan differs by CEFR level, weak skills, profession/sphere, and interests (preset + free text). |
| **Maximum practice** | Most minutes = speaking, listening, exercises, dialogue — not passive reading. |
| **High-quality theory** | Rules as clear bilingual tables + real examples; no invented words; 🔊 on every EN phrase. |
| **Motivation & focus** | Progress feels real; roadmap shows *you can get there*; streaks/XP support habit, not replace substance. |
| **Interactive by default** | Warmup = quiz; episode = many step types; bonus = roulette/review — not «read and tap OK». |
| **Cool tutor energy** | Spirit + serial story + human facts/tips; warm tone; grammar always on; bilingual replies. |

**Non-goal:** a different serial plot per user. **One story for everyone**; personalization is *how* they practice inside that story.

---

## 2. What we have today (baseline)

| Area | Current behavior | Gap |
|------|------------------|-----|
| Daily plan | `study_app/services/daily_plan.py` — warmup fact + episode + optional word bonus | `daily_minutes` on profile **unused**; no rest-day logic |
| Progress UI | `●●●○○○ 1/2` style bar in `handlers._format_daily_plan_text` | Feels like a tiny checklist, not a chapter journey |
| Warmup | Passive read of fact/phrase (`daily_facts.py`) | No quiz, no micro-practice |
| Onboarding | Goal → interests (incl. custom) → sphere → diagnostic | No **20/30/60 min**, no **days/week**, no **Sunday rest** |
| Personalization | Interest hint in greeting; sphere exercises in episodes; level from diagnostic | Not wired into **block count / duration / difficulty mix** |
| Roadmap | XP level + CEFR in profile | No «~2 months to B1» style motivation map |
| Rules | Library + level-filtered map | Not in daily checklist (by design); drill via 📖 Правила |

**Invariant:** existing flows (🔊 TTS, STT, Spirit tutor, lesson engine) must keep working while v2 ships incrementally.

---

## 3. Target experience (v2)

### 3.1 Learner profile inputs (plan sizing)

Stored on `UserProfile` (some fields exist, some new):

| Field | Values | Used for |
|-------|--------|----------|
| `cefr_level` | A0–C2 | Content difficulty, rules map, exercise variants |
| `learning_goal` + `learning_goal_custom` | preset + text | Tone, example domains |
| `profession` + `profession_custom` | preset + text | Sphere exercises, vocab bias |
| `interests` + `interests_custom` | M2M + comma text | Episode hooks, AI personalize, warmup topics |
| `daily_minutes` | **20 / 30 / 60** (onboarding + profile edit) | How many blocks & exercise depth per day |
| `study_days_per_week` | **3–7** | Reminder cadence, streak rules |
| `rest_weekday` | **0=Mon … 6=Sun**, default **6 (Sunday)** | Rest day copy + lighter or off plan |

### 3.2 Daily chapter composition (by `daily_minutes`)

All chapters share the **same spine** (serial episode). Optional blocks scale with time budget.

| Block | ~minutes | 20 min | 30 min | 60 min | Interactive? |
|-------|----------|--------|--------|--------|----------------|
| **Warmup quiz** | 2–3 | ✅ | ✅ | ✅ | MC / gap / listen-pick on fact or phrase |
| **Episode** | 8–25 | ✅ (short path) | ✅ (full) | ✅ (+ extra exercises) | story, vocab, rules, 3–8 exercises, speaking |
| **Listening bite** | 3–5 | — | ✅ | ✅ | 2–3 lines dialogue + comprehension Q |
| **Rule drill** | 3–5 | — | optional | ✅ | 3–5 items from user's level, not yet ✅ |
| **Word review (SRS)** | 2–8 | if due | if due | ✅ expanded | flashcard / gap / speak |
| **Review roulette** | 2–4 | — | — | ✅ | random mix: rule, word, phrase from week |
| **Motivation close** | 0.5 | ✅ | ✅ | ✅ | «+XP today», streak, tomorrow tease |

**Rest day (Sunday by default):** no new episode; optional ~5 min light warmup. Streak **freezes** (does not break).

### 3.3 Progress UX (replace weak checklist feel)

**Today screen header:**

```
📖 Глава дня · Эпизод 4
━━━━━━━━━━━━░░░░  58%  ·  ~22 из 30 мин
```

- **Percent** = weighted by block target minutes (not just 1/2 items).
- **Step list** keeps numbered route but adds icons + time per block.
- **Single CTA** `▶️ Продолжить` unchanged (invariant: no lesson picker paralysis).

### 3.4 Roadmap screen (Phase 3)

New entry from **📊 Прогресс** or profile:

- Current CEFR → next milestone (e.g. A2 → B1).
- **Realistic timeline** from `study_days_per_week` × `daily_minutes` × curriculum size (heuristic, not a promise).
- Visual «map»: completed episodes, next rules unlock, estimated weeks.
- Copy: honest ranges — «при 30 мин / 5 дней ≈ 8–12 недель до B1» with assumptions footnote.

---

## 4. Implementation phases

### Phase 1 — Quick UX *(this week)*

**Goal:** visible improvement without schema risk.

| Task | Files (likely) | Acceptance |
|------|----------------|------------|
| Weighted progress bar (% + minutes) | `handlers._format_daily_plan_text`, `daily_plan._structured_plan` | Bar reflects minutes, not only block count |
| Richer step labels | same + `daily_facts` | Each step shows icon, title, time, XP |
| Interactive warmup v1 | `handlers._show_warmup`, new `study_app/warmup_quiz.py` | 1 MC or gap after fact; 🔊 on EN; marks block done on correct |
| Warmup completion in plan | `daily_plan.py` | `warmup.done` only after quiz, not on open |

**Do not break:** 🔊 on warmup EN; lesson flow after warmup.

### Phase 2 — Onboarding + plan sizing *(with Phase 1)*

**Goal:** `daily_minutes` and schedule drive real plans.

| Task | Files (likely) | Acceptance |
|------|----------------|------------|
| Onboarding step: daily time | `handlers` onboarding, `keyboards`, `db` | 20 / 30 / 60 after sphere |
| Onboarding: days/week + rest day | migration on `UserProfile`, onboarding UI | Default Sun rest; 5 days/week typical |
| `build_or_get_daily_plan` uses minutes | `daily_plan.py` | 20 min → fewer optional blocks; 60 → listening + roulette |
| Profile edit for schedule | `show_profile`, settings keyboard | User can change later |
| Reminders respect rest day | `send_reminders.py` | No nag on rest (or soft message) |

**Migration:** default existing users to `daily_minutes=20`, `study_days_per_week=5`, `rest_weekday=6`.

### Phase 3 — Roadmap & motivation map

| Task | Files (likely) | Acceptance |
|------|----------------|------------|
| `study_app/services/roadmap.py` | new | ETA heuristic from profile + progress |
| Roadmap UI handler | `handlers.show_progress` or new screen | Map + next milestone + assumptions |
| Episode/rule unlock preview | tie to `LessonProgress`, `UserRule` | Shows what opens next |

### Phase 4 — Content depth *(ongoing, parallel)*

- Listening dialogue blocks in curriculum.
- `level_variants` on exercises inside same episode.
- Expand `daily_facts` + quiz bank.
- Rule drill generator from `GrammarRule` + user level.

---

## 5. Personalization matrix

How inputs combine (for implementers & content):

```
cefr_level     → lesson queryset, rule map, exercise difficulty
weak_skills    → extra drill weight (future: diagnostic tags)
profession     → personalized exercise step + AI examples
interests      → greeting hint, warmup topic bias, AI personalize
daily_minutes  → which optional blocks appear + episode depth flag
study_days     → reminders + roadmap ETA
```

**Custom text fields** (`interests_custom`, `profession_custom`, `learning_goal_custom`) must be parsed and passed to `ai_app/services/personalize.py` — never ignored if non-empty.

---

## 6. Safe change protocol

When implementing any phase:

1. Read [`PRODUCT_INVARIANTS.md`](PRODUCT_INVARIANTS.md).
2. Additive DB migrations only; sane defaults for existing users.
3. Feature-flag optional blocks behind profile fields where risky.
4. Run tests: `LessonTTSTests`, `BilingualSTTTests`, new `DailyPlanV2Tests` when added.
5. Manual smoke: `/start` → onboarding → **Учиться** → warmup quiz → episode → 🔊.

**Rollback:** each phase shippable independently; Phase 1 does not require new DB columns.

---

## 7. Owner decisions (locked 2026-07-07)

| Topic | Decision |
|-------|----------|
| **Rest day** | Optional **light warmup only** (~5 min), no new episode |
| **Streak on rest day** | **Freeze** — rest does not break streak |
| **20 min plan** | Skip listening block (ultra-short plans stay focused on episode) |
| **Roadmap ETA** | Show **range** (e.g. «8–12 weeks to B1») with assumptions footnote |

---

## 8. Success metrics (qualitative)

After Phase 1+2 ship, owner review:

- [ ] «Учиться» screen feels like a **training session**, not `1/2` checklist.
- [ ] Warmup requires **one tap answer**, not only reading.
- [ ] New user sets **30 min / 5 days** and sees **~30 min route**.
- [ ] Interests custom text visible in plan greeting or warmup topic.
- [ ] Spirit, TTS, STT, lessons unchanged from [`PRODUCT_INVARIANTS.md`](PRODUCT_INVARIANTS.md).

---

## 9. Changelog

| Date | Change |
|------|--------|
| 2026-07-07 | Initial spec; agreed order: **Phase 1 + 2**, then **Phase 3** |
