# Program vision — Phase 4+ (locked direction)

**Last updated:** 2026-07-07  
**Owner:** product direction from Maria's feedback session.

## North star

App scope: **A1 → C1** (stretch C2). One serial story; personalization via plan, focus, and practice mix.

## What shipped in this session

| Item | Where |
|------|--------|
| Goal level (B1–C2) | 👤 Профиль → 🎯 Цель уровня |
| Skill focus (speaking, listening, …) | 👤 Профиль → 💪 Фокус практики |
| Full journey map + **months to goal** | 📊 Прогресс or 👤 → 🗺 Карта пути |
| Spirit truncation fix | tutor uses full token budget |
| Phrase practice from chat | «потренировать эту фразу» in 💬 Наставник |
| Diagnostic listening items | seed_content (A2, B1, B2) |

## Still to build (Phase 4 content + accuracy)

1. **More episodes** per level (A1–C1) — curriculum.py
2. **Level variants** inside same episode
3. **Listening blocks** in daily plan (partially started)
4. **Diagnostic v2** — more listening + speaking anxiety questions after test
5. **Onboarding** — ask goal level + skill focus (not only profile edit)
6. **Daily plan** weights more speaking when `skill_focus` includes speaking

## Learner types we support

| Profile | Program bias |
|---------|----------------|
| B2 on paper, afraid to speak | +speaking in focus → more voice steps, tutor, less MC |
| Wants C1 from B2 | roadmap shows months to C1 with planned curriculum size |
| Wants tests / gaps | phrase practice + rule drills + exercises in episodes |

## Invariants

Do not break: TTS on all EN, STT dual-pass, Spirit grammar block, product invariants doc.
