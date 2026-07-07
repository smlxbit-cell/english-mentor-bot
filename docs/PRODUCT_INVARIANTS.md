# Product Invariants — Do Not Break

**Last updated:** 2026-07-07  
**Purpose:** Locked rules agreed with the product owner. **Read this before any change**
to voice, lessons, tutor, STT/TTS, or prompts. If a fix would violate an invariant,
fix it another way or extend — never remove.

**Related:** `docs/PRODUCT_CONCEPT.md`, `docs/PROGRAM_STRUCTURE.md`, `docs/TARIFFS.md`

---

## 0. Meta-rule (most important)

> **When you change one thing, you must not break what already works.**

Before shipping:

1. Re-read this file.
2. Identify which invariants your change touches.
3. Manually verify the affected flows (or run tests).
4. If you remove a code path, confirm nothing in §1–§8 depended on it.

---

## 1. Voice & TTS — every English phrase is listenable

| Rule | Detail |
|------|--------|
| **🔊 on all English** | Any screen that shows English text must offer **🔊 Слушать** (or auto-play for `audio` steps). Lessons, diagnostic, exercises, dictionary, rules, daily plan, tutor. |
| **Mixed RU+EN steps** | Lesson hooks/stories use `🇬🇧 English line` inside Russian text. TTS must extract English via `_english_text_for_tts()` / `_speak_text_for_step()` — **not** require the whole step to be English. |
| **Explicit override** | `content.speak_en` still wins when set; extraction is the fallback. |
| **Auto-voice** | Lesson steps with English (`hook`, `story`, `dialogue`, `vocabulary`, `grammar_note`) **auto-send a voice message** after the text, plus **🔊 Слушать** for replay. |
| **Provider** | Try AITUNNEL `OPENAI_*` (`gpt-4o-mini-tts`) when the API key allows it; **always fall back to `edge`** (free). Lessons must voice even when AITUNNEL blocks TTS models. |
| **Import** | `from ai_app.tts import get_tts_provider` — missing import = silent TTS failure. |

**Key files:** `telegram_app/bot/handlers.py` (`_speak_text_for_step`, `_english_text_for_tts`, `_render_step`), `telegram_app/bot/keyboards.py`, `ai_app/tts/`

**Regression test:** `telegram_app/tests.py` → `LessonTTSTests`

---

## 2. Speech recognition (STT)

| Rule | Detail |
|------|--------|
| **Tutor voice** | Always dual-pass **RU + EN** Whisper, then `merge_tutor_transcripts()`. |
| **Default model** | `whisper-large-v3-turbo` for **all subscription tiers** unless the AITUNNEL key explicitly allows another model. |
| **Fallback chain** | `_whisper_model_candidates()`: tier model → `OPENAI_WHISPER_MODEL` → `OPENAI_WHISPER_FALLBACK_MODELS`. Never skip the env default. |
| **Forbidden default** | Do **not** put `gpt-4o-mini-transcribe` in fallback defaults or as Pro primary until verified on the live API key. |
| **Yandex** | `STT_YANDEX_FALLBACK=false` = AITUNNEL-only. Only disable Yandex when Whisper fallback chain is reliable. |
| **Soft failures** | STT errors → log + empty transcript; user message mentions **STT/Whisper**, not TTS. |
| **Code-switch** | Keep `is_pure_russian_speech()`, phantom EN/RU drop, scaffold repairs in `bilingual.py`. Pure Russian → **no EN line** (drop Polish/Latin junk from EN pass). |

**Key files:** `ai_app/speech/whisper.py`, `ai_app/speech/bilingual.py`, `ai_app/speech/registry.py`, `billing_app/plans_catalog.py`

---

## 3. Tutor (💬 Наставник / Spirit)

| Rule | Detail |
|------|--------|
| **Grammar always on** | Voice/text tutor replies **must** include: Услышал → Грамматика (gentle) → Слово → Ещё можно сказать → Spirit answer. **Never** replace grammar with spirit_chat-only. |
| **Full-sentence grading** | Услышал and Грамматика must cover the **entire** learner utterance (all clauses after *like*, *when*, *or*), not just the first half. Never «✅ верно» if only the opening was checked. |
| **Grammar follow-up** | When the learner asks to explain a **previous** sentence («explain the sentence I said», «разбери подробнее»), Spirit must use `tutor_history` and explain the **target sentence** from the prior turn — not only grade the new meta-question. |
| **Bilingual replies** | Every English phrase shown to the user needs Russian in a **🇷🇺** block (`TRANSLATION RULE` in prompts). |
| **Spirit persona** | Magical tutor «Спирит» — biography, dialogue, daily stories (`spirit_character.py`). Warm tone; no harsh ❌ on STT noise, duplicates, apostrophes, or forgotten words. |
| **Real English only** | Tutor/Spirit must **not** invent English words or teach internet neologisms (e.g. *sonder*, *vellichor* from Dictionary of Obscure Sorrows) as learnable vocabulary. Use established dictionary English; explain concepts in Russian or with real phrases. |
| **Rule tablets** | Re-show grammar rule tablets on voice turns when there are substantive mistakes. |
| **TTS on tutor** | `🔊 Слушать` on every tutor reply that contains English (`_english_text_for_tts`, `last_tutor_tts` fallback). |

**Key files:** `ai_app/services/prompts.py`, `ai_app/services/spirit_character.py`, `telegram_app/bot/handlers.py` (`_tutor_reply`, `_transcribe_tutor_voice`)

---

## 4. Lessons & content

| Rule | Detail |
|------|--------|
| **Bilingual everywhere** | EN phrase + RU translation in lessons, rules, vocabulary, dialogue. |
| **Grammar tables** | `grammar_note` steps: table-first HTML, `rule_key` → Rules Library. |
| **TTS on steps** | vocabulary → words+examples; dialogue → all EN lines; hook/story → extract `🇬🇧` lines. |
| **Curriculum data** | `content_app/curriculum.py` — adding episodes must not drop `speak_en` where explicit audio is needed, but extraction covers `🇬🇧` lines without it. |

---

## 5. Infrastructure

| Rule | Detail |
|------|--------|
| **Production** | Server `109.71.244.197`, path `/home/mentor/english-mentor-bot`, systemd `english-mentor-bot`. |
| **Deploy** | `scp` changed files + `systemctl restart english-mentor-bot`. |
| **Do not** | Run the bot locally while the server instance is active (Telegram conflict). |
| **Secrets** | Never commit `.env`. Never paste API keys in chat. |
| **AITUNNEL key whitelist** | If «Разрешённые модели» is set on the API key, it must include **chat + STT + TTS** slugs (see below). Only `gpt-4o-mini` → voice returns **403** and nothing works. Empty whitelist = all models allowed. |

**Minimum models to allow on an AITUNNEL key (one per line):**

```
gpt-4o-mini
whisper-large-v3-turbo
gpt-4o-mini-tts
```

Optional fallbacks: `whisper-large-v3`, `whisper-1`, `gpt-4.1-mini`, `gpt-4.1-nano`.

---

## 6. Tariffs & limits

| Rule | Detail |
|------|--------|
| **Plans** | `billing_app/plans_catalog.py` is source of truth; sync via `seed_subscription_plans`. |
| **STT per tier** | Documented in `docs/TARIFFS.md`. Code must match catalog after seed. |
| **Voice minutes** | Enforced per subscription; tutor AI limits separate from voice minutes. |

---

## 7. Checklist before merging voice/tutor/lesson changes

- [ ] Lesson step with `🇬🇧` line shows **🔊 Слушать**
- [ ] Tutor voice: STT works (Whisper turbo fallback chain)
- [ ] Tutor reply: grammar block + 🇷🇺 translation + **🔊 Слушать**
- [ ] TTS synthesizes via AITUNNEL (`get_tts_provider` imported)
- [ ] No new hard ❌ on benign STT artifacts
- [ ] Tests pass: `telegram_app.tests.LessonTTSTests`, `ai_app.tests.WhisperSTTTests`, `ai_app.tests.BilingualSTTTests`
- [ ] Server bot restarted after deploy

---

## 8. Change log (invariant updates)

| Date | Change |
|------|--------|
| 2026-07-07 | Initial document: TTS on all English, STT fallback fix, Spirit/grammar rules, meta-rule |

When the product owner adds a new rule, **append here and update `.cursor/rules/product-invariants.mdc`**.
