# Words section — navigation & logic (LOCKED)

**Status:** agreed with product owner, 2026-08-25  
**Purpose:** canonical map for **🎯 Тренировка → Слова**, dictionary browse, and word drill.  
**Do not remove or “simplify” flows here without explicit owner approval.**

**Code entry points:** `telegram_app/bot/handlers.py`, `telegram_app/bot/keyboards.py`,  
`learning/word_bank/service.py`, `telegram_app/bot/db.py`

**Related:** `docs/WORD_BANK.md`, `docs/WORD_BANK_INTEGRATION.md`, `docs/PRODUCT_INVARIANTS.md` §9

---

## 0. Product intent (why this exists)

The learner builds a **personal training pile** («📗 Учить») and practices from it — not from random A1 junk when they are B2.

Three separate ideas — **do not merge**:

| Idea | Meaning |
|------|---------|
| **Bank corpus** | Global `WordBankEntry` A1–C1 (~5000 conversational words) |
| **Personal marks** | User marks: ✅ Знаю / 🎯 Учить / ⏭️ Позже → `UserWordBankStatus` |
| **Training pile** | Words marked **Учить** — what drills and «🎯 Тренировка» consume |

The dictionary is the **main front door** to fill the pile by hand. The daily program **reads** from the pile; it must not spam new words when the pile is already big.

---

## 1. Entry & hub

**Entry:** 🎯 Тренировка → Слова → `words:hub`

| Button | Callback | Meaning |
|--------|----------|---------|
| 🎯 Тренировка · N | `words:repeat` | Practice up to **10** words from «Учить» pile (see §6) |
| 📘 Новые слова | `words:new` | Add words manually — **no** redundant «Начать · 10» on this screen |

Hub shows level progress bars. User level is visible; do not hide it.

---

## 2. 📘 Новые слова (`words:new`)

Compact picker — **3 buttons**, straight to action:

| Button | Callback | Action |
|--------|----------|--------|
| 📊 Уровни | `words:bank` | Dictionary browse by CEFR level |
| 👀 Знаю? | `words:survey:menu` | Quick level survey |
| 🔍 Поиск | `words:search` | Search EN/RU |
| ← Слова | `words:hub` | Back |

**Do not** insert an extra «Начать · 10» step here — user goes directly to levels / survey / search.

Optional legacy path `words:learn:daily` (10 random unseen at user level) may exist in code but is **not** the primary dictionary entry.

---

## 3. 📖 Словарь · по уровню (`words:bank`)

### 3.1 Level picker

Text: «Ваш уровень: **B2**» (user CEFR).

Level buttons: `A1` `A2` `B1` `B2` `C1` — **current user level gets ★**

Example: user is B2 → button label **`B2 ★`**, not plain `B2`.

Implementation: `word_bank_menu_kb(user_level)` — same ★ rule as `word_survey_levels_kb`.

### 3.2 Level page (e.g. B1, 6 unseen words)

Shows unseen words at that level (paginated). Header may show global `📗 учить N` — that is **info only**.

**Button order (top → bottom) — LOCKED:**

| # | Button | Meaning |
|---|--------|---------|
| 1 | **🎯 Тренировка · {page_count}** \| **▶️ По одному** | Same row — drill page or card survey |
| 2 | **✅ Знаю** \| **🎯 Учить** | Mark whole page |
| 3 | ◀️ / ▶️ pagination | |
| 4 | ← Уровни | |

Callback for page training: `words:bank:page:train:{level}:{page}`  
On start: mark page words as **Учить**, then **pre-drill intro** (§4.0), then word drill.

**Never** show `🎯 Тренировка · {global_learning_count}` on the dictionary page list. Global training lives on hub / «Мои слова», not here.

### 3.3 «▶️ По одному» survey (page or level)

Per word: ✅ Знаю / 🎯 Учить (+ optional ⏭️ Позже).

Track **session** counts separately from global pile:

- `word_survey_session_known` — marked Знаю this session  
- `word_survey_session_learn` — marked Учить this session  

**Finish screen (when queue empty):**

```
✅ 6 слов готово
✅ знаю 2 · 📗 учить 4

Сразу тренировка 👇
[ 🎯 Тренировка · 4 ]   ← session learn count ONLY
[ ← К списку ]
[ ← Слова ]
```

Callback: `words:survey:train` — drills **only** `word_survey_session_learn`, not entire «Учить» bank.

If user marked only «Знаю» → no training button; explain that «Учить» is needed for drill.

---

## 4. Word drill (training session)

Entry paths:

- Hub `words:repeat` / `srs:start` → up to 10 from «Учить» pile (§6)  
- Page training `words:bank:page:train:…`  
- Survey finish `words:survey:train`  
- Daily plan words block (from existing pile — §6)  

### 4.0 Pre-drill intro pass — LOCKED (all training entry paths)

Before the translation quiz, **always** show one card per word:

- Header `📘 N/M · LEVEL` (M = session size: page count, pile batch, survey session, etc.)  
- 🇬🇧 word + 🇷🇺 translation + 📝 example (EN + RU)  
- Auto 🔊 TTS (headword + example)  
- Buttons: **🎯 Учить** \| **✅ Знаю** (+ ← Выход)  

Applies to **every** training launch:

- Hub `words:repeat` / `srs:start`  
- Daily plan words block  
- Dictionary page `words:bank:page:train:…`  
- Survey finish `words:survey:train`  

**Do not** skip this pass to “save taps” — learner must see/hear the word before being quizzed.

After intro: summary `✅ Знаю X · учить Y → тест`, then drill. Words marked **Знаю** in intro leave the session; only **Учить** words go to the quiz.

Drill steps: context / listening / meaning / recall (see `learning/word_bank/drill.py`).

### 4.1 Cards must show

- EN word + 🔊 TTS  
- 🇷🇺 translation (sanitized — no English definition blobs under 🇷🇺)  
- 📝 example EN + **(RU)** under every example on intro and feedback cards  

### 4.2 Post-drill final pass — LOCKED

After «🎉 Тренировка завершена!» **always** show one more **Знаю / Учить** pass over the words just drilled:

1. Header: «👀 Финальный проход — что уже точно знаешь?»  
2. Same card UI as survey (✅ Знаю / 🎯 Учить)  
3. **Знаю** → `UserWordBankStatus.KNOWN` — word leaves «Учить» pile  
4. **Учить** → stays in «Учить» pile  
5. Summary: `✅ знаю X · 📗 учить Y` → hub or daily plan  

Mode: `word_drill_review`. This is how the pile **shrinks** after real practice.

**Do not** skip this pass to “save taps” — owner uses it to curate the pile.

---

## 5. «📗 Учить» pile — queue policy (LOCKED)

Constants (`learning/word_bank/service.py`):

- `DAILY_NEW_WORDS = 10` — words per training session / daily recommendation  
- `MIN_LEARNING_QUEUE = 10` — minimum words in «Учить»  

### 5.1 Auto top-up — only when pile is small

Function: `ensure_min_learning_queue(user_id, user_level, interests)`.

| Situation | Bot behaviour |
|-----------|---------------|
| «Учить» **≥ 10** | **Do nothing** — no daily spam (even if user has 79 or 100) |
| «Учить» **< 10** | Add **only** `(10 − current)` unseen words at **user CEFR level**, prefer **interest topics** |
| User learned 5 today | Tomorrow add 5 more → maintain ~10 minimum |

Words added by auto top-up are marked **Учить** immediately.

**Never** push another 10 every day on top of a pile the user built manually in the dictionary.

### 5.2 Where training pulls words from

Function: `pick_training_words(user_id, user_level, limit=10)`.

Order:

1. Due SRS words from «Учить» pile (`UserWordProgress`)  
2. Any remaining «Учить» words (any level the user marked — respect their choices)  

**Do not** fall back to random unseen words when pile ≥ 10.  
**Do not** pull A1 words for a B2 user via fallback when pile is empty — show «Отметьте слова в 📖 Словарь».

`ensure_min_learning_queue` runs before hub training / `srs:start` so empty users get 10 first.

### 5.3 Daily program words block

When user opens **plan → words**:

- Take up to 10 from **existing** «Учить» pile (`pick_training_words`)  
- **Do not** auto-import 10 new plan words into the pile each day  

Plan consumes the pile; dictionary + min-top-up refills it.

---

## 6. 🎯 Тренировка from hub (`words:repeat`)

1. `ensure_min_learning_queue` if pile < 10  
2. `pick_training_words` → up to 10 words  
3. **Pre-drill intro pass** (§4.0) — Знаю / Учить + example + 🔊 on each word  
4. Word drill (translation etc.)  
5. Post-drill final pass (§4.2)  

Button label «🎯 Тренировка · N» on hub / repeat section: **N = min(learning_count, 10)** for display — session size, not total pile size.

---

## 7. 📗 Мои слова (`words:mydict`)

Personal lists: Учить / Уже знаю / темы / уровни.

Global «🎯 Тренировка · N» **is allowed** here (full pile) — unlike dictionary page list (§3.2).

---

## 8. Practice level filter

Words shown in training must match user intent:

- **Fallback unseen picks** (top-up only): user **CEFR level only** — not lower levels  
- **Pile drill**: all words user marked Учить (they chose the level in dictionary)  

Regression: B2 user must not see random A1 in training after this rule set.

---

## 9. UI wording (locked)

| ✅ Use | ❌ Avoid |
|--------|---------|
| Словарь, Учить, Знаю, Тренировка | «банк», «повтор», internal callback names in UI |
| 🎯 Тренировка · N (session/page scope) | Global pile count on dictionary page |
| ★ on user's level in level pickers | Plain level buttons without marker |

---

## 10. Key files & functions

| Area | File | Symbols |
|------|------|---------|
| Keyboards | `telegram_app/bot/keyboards.py` | `word_bank_menu_kb`, `word_bank_list_page_kb`, `word_survey_finish_kb` |
| Handlers | `telegram_app/bot/handlers.py` | `_show_bank_page`, `start_word_survey_for_page`, `_finish_word_drill`, `_show_word_drill_review_card`, `_start_practice_flow`, `_start_practice_intro`, `start_page_word_training`, `start_survey_session_training` |
| Queue logic | `learning/word_bank/service.py` | `ensure_min_learning_queue`, `pick_training_words`, `MIN_LEARNING_QUEUE`, `get_review_words_for_dicts` |
| Display | `learning/word_bank/translation_enrich.py` | `sanitize_translation_for_display` |
| Drill cards | `learning/word_bank/drill.py` | `format_intro_card`, `append_example_lines` |

---

## 11. Smoke checklist (before ship)

- [ ] Dictionary level menu: user level has **★**  
- [ ] B1 page: **🎯 Тренировка · 6** (page size), not · 79  
- [ ] Survey finish: train button uses **session** learn count  
- [ ] **Any** training entry (hub, dictionary page, survey): pre-drill intro (📘 card, example, 🔊, **Знаю / Учить**) before quiz  
- [ ] After drill: final **Знаю / Учить** pass appears  
- [ ] Pile ≥ 10: no auto-add on hub visit  
- [ ] Pile < 10: top-up to 10 at user level + interests  
- [ ] B2 training: no stray A1 from fallback  
- [ ] Every EN card: 🔊 + example **(RU)**  
- [ ] No **2-letter junk** (`ab`, `ac`) in dictionary browse  
- [ ] Countries: **Afghanistan — Афганистан** (capitalized EN + RU)  
- [ ] Deploy + `systemctl restart english-mentor-bot`

---

## 12. Word bank quality (LOCKED)

| Rule | Detail |
|------|--------|
| **No abbreviations** | Headwords like `ab`, `ac` must never appear — filter in `word_quality.py`, purge via `purge_junk_headwords`. |
| **Conversational only** | Medical/technical junk filtered; supplements must pass `filter_row`. |
| **Proper nouns** | EN + RU capitalized via `english_display.py` (`ALWAYS_CAP`, `part_of_speech=proper noun`). |
| **After seed / expand** | Run `purge_junk_headwords` + `fix_translations` on prod. |

**Do not weaken `word_quality.py` to “fill quotas” without owner approval.**

---

## 13. Change log

| Date | Change |
|------|--------|
| 2026-08-25 | Locked: page-scoped training, ★ level marker, survey session train, post-drill review, min-10 queue policy, no daily pile spam |
| 2026-08-26 | Word bank quality: no 2-letter abbreviations; proper-noun capitalization |
| earlier | Initial nav map (hub / новые / повтор) |

When owner changes behaviour, **update this file first**, then code, then `PRODUCT_INVARIANTS.md` §9.
