# Карта грамматики A1→C1 (полный банк)

Единый план **всех ключевых правил** для 🎓 Грамматика, дневного плана и эпизодов.

**Почему раньше было «мало»:** в `rules_bank.py` лежал **стартовый MVP** (~23 карточки), чтобы проверить UX. Это **не** полный объём грамматики. Ниже — целевая карта на **~380 правил** (A1–C1).

**Уровни в боте:** только **A1 · A2 · B1 · B2 · C1**. C2 в продукте нет — в карту не входит.

**Легенда:** ✅ уже в банке · 🖼 нужна картинка Spirit · ⬜ запланировано

---

## Навигация (LOCKED): 5 разделов на каждом уровне

Один и тот же каркас меню — ученик не переучивается:

| # | Slug | Раздел | Что внутри |
|---|------|--------|------------|
| 1 | `phrases` | 👋 **Фразы и общение** | приветствия, вежливость, кафе, отель, работа, телефон, мнения |
| 2 | `verbs` | ⚡ **Глаголы и времена** | to be, времена, модальные, пассив, perfect, gerund/infinitive |
| 3 | `words` | 📝 **Слова и формы** | артикли, число, местоимения, прилагательные, quantifiers |
| 4 | `links` | 🔗 **Предлоги и связки** | in/on/at, because/so, although, linkers по уровню |
| 5 | `syntax` | 🧩 **Предложение и вопросы** | порядок слов, вопросы, отрицание, условия, придаточные |

**Путь:** Справочник → Уровень → **один из 5 разделов** → список правил → карточка (🖼 + таблица + 🔊).

Код: `learning/grammar/categories.py`.

---

## Сводка: сколько правил нужно

| Уровень | 👋 | ⚡ | 📝 | 🔗 | 🧩 | **Итого** | ✅ сейчас |
|---------|----|----|----|----|-----|-----------|----------|
| **A1** | 14 | 18 | 16 | 10 | 12 | **70** | 11 |
| **A2** | 16 | 24 | 18 | 14 | 18 | **90** | 10 |
| **B1** | 14 | 28 | 16 | 12 | 22 | **92** | 3 |
| **B2** | 12 | 32 | 14 | 12 | 24 | **94** | 1 |
| **C1** | 10 | 26 | 10 | 10 | 20 | **76** | 0 |
| **ВСЕГО** | **66** | **128** | **74** | **58** | **96** | **422** | **25** |

**Округлённая цель для производства: ~380–420 карточек** (одна карточка = одно правило = одна таблица + примеры + одна картинка Spirit).

### Языковой стандарт (LOCKED)

- **Основной курс: American English** — разговорный, распространённый US.
- **British** — только в **`tip_ru`** с пометкой 🇬🇧, если форма заметно отличается (have got, lift/elevator и т.д.).
- Отдельные «британские уроки» — позже, не смешиваем в основной таблице.

> Правило **узкое и ёмкое**: 3–5 строк таблицы, 1–2 примера, 1 tip.  
> Не «Present Simple целиком», а «Present Simple: he/she +s», «Questions: Do you…?» — отдельные карточки.

---

## A1 — 70 правил

### 👋 Фразы и общение (14)

| # | key (план) | Тема |
|---|------------|------|
| 1 | `greetings-hello` ✅ | Hello / Hi / Good morning |
| 2 | `greetings-goodbye` ✅ | Goodbye / See you |
| 3 | `polite-requests` ✅ | I would like… / please |
| 4 | `thank-you-responses` ✅ | Thank you / You're welcome |
| 5 | `sorry-excuse-me` ⬜ | Sorry / Excuse me / Pardon |
| 6 | `yes-no-ok` ⬜ | Yes / No / OK / Sure |
| 7 | `introducing-yourself` ⬜ | My name is… / Nice to meet you |
| 8 | `numbers-1-20` ⬜ | Numbers 1–20 |
| 9 | `numbers-21-100` ⬜ | 21–100 · How many? |
| 10 | `time-oclock` ⬜ | What time is it? · o'clock |
| 11 | `days-months` ⬜ | Monday… / January… |
| 12 | `cafe-order-basic` ⬜ | A coffee, please |
| 13 | `how-are-you` ⬜ | How are you? · Fine, thanks |
| 14 | `good-night` ⬜ | Good night / Sleep well |

### ⚡ Глаголы и времена (18)

| # | key | Тема |
|---|-----|------|
| 1 | `to-be-basics` ✅ 🖼 | I am / you are / he is |
| 2 | `to-be-negative` ✅ 🖼 | am not / isn't / aren't |
| 3 | `to-be-questions` ✅ 🖼 | Am I…? / Are you…? |
| 4 | `to-be-short-forms` ✅ 🖼 | I'm / you're / he's |
| 5 | `there-is-are-affirm` ⬜ | There is / There are |
| 6 | `there-is-are-questions` ⬜ | Is there…? / Are there…? |
| 7 | `have-got-affirm` ⬜ | I have got / She has got |
| 8 | `have-got-questions` ⬜ | Have you got…? |
| 9 | `imperatives-affirm` ⬜ | Open the door. / Sit down. |
| 10 | `imperatives-negative` ⬜ | Don't run! / Don't worry. |
| 11 | `can-ability` ⬜ | I can swim |
| 12 | `can-permission` ⬜ | Can I…? |
| 13 | `can-negative` ⬜ | can't |
| 14 | `present-simple-i-you` ⬜ | I work / You live (факты) |
| 15 | `present-simple-he-s` ⬜ | He works (+s) |
| 16 | `like-love-ing` ⬜ | I like reading (intro) |
| 17 | `want-would-like` ⬜ | I want / I'd like |
| 18 | `lets` ⬜ | Let's go |

### 📝 Слова и формы (16)

| # | key | Тема |
|---|-----|------|
| 1 | `articles-a-an` ✅ | a / an |
| 2 | `plural-s` ✅ | +s |
| 3 | `plural-es` ⬜ | +es (boxes) |
| 4 | `plural-ies` ⬜ | babies, cities |
| 5 | `demonstratives-this-that` ✅ | this / that |
| 6 | `demonstratives-these-those` ⬜ | these / those |
| 7 | `possessives-my-your` ✅ | my / your |
| 8 | `possessives-his-her` ⬜ | his / her / its |
| 9 | `possessive-s` ⬜ | John's book |
| 10 | `adjective-before-noun` ⬜ | a big house |
| 11 | `article-the-basic` ⬜ | the — первое знакомство |
| 12 | `some-any-basic` ⬜ | some water / any questions? |
| 13 | `much-many-basic` ⬜ | How many? / How much? |
| 14 | `countable-uncountable-a1` ⬜ | apple vs water |
| 15 | `object-pronouns` ⬜ | me / him / them |
| 16 | `possessive-pronouns` ⬜ | mine / yours |

### 🔗 Предлоги и связки (10)

| # | key | Тема |
|---|-----|------|
| 1 | `prep-in-on-at-place` ⬜ | in the box / on the table / at home |
| 2 | `prep-in-on-at-time` ⬜ | in May / on Monday / at 5 |
| 3 | `prep-under-behind` ⬜ | under / behind / next to |
| 4 | `prep-to-from` ⬜ | to school / from work |
| 5 | `and-but` ⬜ | and / but |
| 6 | `because-so` ⬜ | because / so |
| 7 | `or` ⬜ | tea or coffee |
| 8 | `with-without` ⬜ | with / without |
| 9 | `for-about` ⬜ | for you / about work |
| 10 | `of` ⬜ | a cup of tea |

### 🧩 Предложение и вопросы (12)

| # | key | Тема |
|---|-----|------|
| 1 | `word-order-svo` ⬜ | Подлежащее → глагол → дополнение |
| 2 | `questions-yes-no` ⬜ | Are you…? / Do you…? |
| 3 | `wh-what-where` ⬜ | What / Where |
| 4 | `wh-who-when` ⬜ | Who / When |
| 5 | `wh-how` ⬜ | How / How old |
| 6 | `how-much-many` ⬜ | How much / How many |
| 7 | `negation-not` ⬜ | not with to be |
| 8 | `negation-dont` ⬜ | don't / doesn't |
| 9 | `there-questions` ⬜ | Is there any…? |
| 10 | `subject-pronouns` ⬜ | I / you / he / she |
| 11 | `question-word-order` ⬜ | Where **do** you live? |
| 12 | `short-answers` ⬜ | Yes, I do. / No, he isn't. |

---

## A2 — 90 правил (структура + объём)

| Раздел | Кол-во | Основные блоки |
|--------|--------|----------------|
| 👋 | 16 | отель ✅, работа ✅, ресторан, магазин, телефон, email, приглашения, советы |
| ⚡ | 24 | Present Simple ✅×2, **Continuous**, **Past Simple** reg/irreg, **going to**, used to, **must/should**, could ✅ |
| 📝 | 18 | сравнительные/превосходные, much/many, some/any детальнее, артикли с географией |
| 🔗 | 14 | предлоги времени/движения, by/until/since (intro), although/before/after |
| 🧩 | 18 | wh ✅, навигация ✅×2, место ✅, question tags, indirect Q intro, so/neither |

**Уже в банке (10):** present-simple-affirmative, present-simple-questions, wh-questions-basics, navigation-where, navigation-directions, prepositions-place, modal-can, modal-could-polite, hotel-check-in, work-small-talk.

**Ещё ~80 карточек** по блокам выше (каждое время: утверждение / отрицание / вопрос = 3 карточки где нужно).

---

## B1 — 92 правила

| Раздел | Кол-во | Основные блоки |
|--------|--------|----------------|
| 👋 | 14 | work-updates ✅, мнения, жалобы, переговоры, презентации |
| ⚡ | 28 | **Past continuous**, **Present perfect** ✅ + since/for, **Past perfect**, will/going to, **passive** present/past, phrasal verbs (6×), gerund vs infinitive |
| 📝 | 16 | relative who/which, quantifiers, both/either/neither |
| 🔗 | 12 | зависимые предлоги (depend on), linkers (however, therefore) |
| 🧩 | 22 | **1st conditional**, **2nd** ✅, reported speech present/past, indirect questions, purpose (to/in order to) |

---

## B2 — 94 правила

| Раздел | Кол-во | Основные блоки |
|--------|--------|----------------|
| 👋 | 12 | formal email, softening, signposting, деловые фразы |
| ⚡ | 32 | perfect continuous, future perfect, **passive modals**, mixed conditionals, wish, suggest+gerund ✅, phrasal verbs (10×) |
| 📝 | 14 | participles bored/boring, emphasis, inversion with adjectives |
| 🔗 | 12 | advanced linkers, prepositions после прилагательных |
| 🧩 | 24 | 3rd conditional, cleft sentences, inversion, non-defining relatives, discourse |

---

## C1 — 76 правил

| Раздел | Кол-во | Основные блоки |
|--------|--------|----------------|
| 👋 | 10 | academic register, hedging in speech, formal complaints |
| ⚡ | 26 | modal deduction (must have), subjunctive, advanced passive, nuance will/would |
| 📝 | 10 | nominalisation, complex noun phrases |
| 🔗 | 10 | subtle connectors, collocation prepositions |
| 🧩 | 20 | fronting, ellipsis, substitution, complex conditionals, stylistic inversion |

---

## Картинки Spirit (на каждое правило)

| Параметр | Значение |
|----------|----------|
| Размер | **1280 × 720 px**, 16:9 |
| Формат | PNG, до 1.5 MB |
| Файл | `{rule_key}.png` |
| Путь | `media/spirit/rules/{rule_key}.png` |

**Процесс:** ты вставляешь картинку в чат → **я** переименовываю в `{rule_key}.jpg` → `media/spirit/rules/` → фото + текст + 🔊.

**Эталон оформления 🖼:** карточка `yes-no-ok` / `numbers-1-20` — Spirit слева + таблица справа, шрифт geometric sans-serif (Inter/Montserrat), без растягивания.

**Redo:** только по твоей загрузке — я не меняю картинки без твоего файла.

### Spirit — визуальный стиль (LOCKED + вариативность)

**Не меняем:** тёмно-синий фон, палитра UI, жёлтые акценты форм, формат таблицы, тот же 3D-Spirit.

**Эталон качества 🖼:** `numbers-1-20` · `greetings-hello` · `to-be-basics` — **всегда прикреплять одну из них как style reference** при генерации.

**Типографика (LOCKED — частая ошибка генератора):**
- Шрифт: **clean sans-serif**, нормальные пропорции букв
- **ЗАПРЕЩЕНО:** vertically stretched text, tall narrow letters, warped Cyrillic
- Таблица: те же отступы, 3 колонки, тонкие серые линии — как на эталоне
- Заголовок правила: **одна строка**, white bold, не «расползаться» по высоте
- Русский перевод: светло-серый, **тот же размер**, что English example

**Меняем (если уместно по теме):** жест, мимика, реквизит (телефон, чашка, часы…).

**Шарф = уровень CEFR:**

| A1 cyan `#22d3ee` | A2 purple `#a78bfa` | B1 amber `#fbbf24` | B2 emerald `#34d399` | C1 coral `#fb7185` |

**Пилоты 🖼:** to-be-basics · to-be-negative · to-be-questions · to-be-short-forms

---

## Производство (очередь)

1. **A1 полностью (70)** — закрепить формат карточки + Spirit  
2. **A2 (90)** — связка с эпизодами  
3. **B1 → B2 → C1** — по карте выше  
4. Параллельно: текст (я) + картинка (ты) + деплой  

**Темп:** ~5–10 правил/неделю → весь банк за **8–12 месяцев** контент-плана.

---

## Что не входит в «правило-карточку»

- Отдельные **phrasal verbs** как словарь (это word bank) — в грамматике только **паттерны** (suggest + gerund, look **after** + object).  
- Чистая **лексика** без грамматического паттерна — в 📖 Словарь.  
- **C2** — вне продукта.

---

## Файлы

- `content_app/rules_bank.py` — данные  
- `learning/grammar/categories.py` — 5 разделов  
- `docs/GRAMMAR_NAV.md` — UX invariants  
- `docs/GRAMMAR_RULES_ROADMAP.md` — этот документ
