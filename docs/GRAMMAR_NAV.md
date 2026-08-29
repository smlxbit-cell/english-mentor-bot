# Grammar rules — navigation & display (LOCKED v1)

Mirror of `WORD_BANK_NAV.md` for the **🎓 Грамматика** section.

## 1. Canonical bank

| Source | Role |
|--------|------|
| `content_app/rules_bank.py` | All rules (A1→C1): key, level, topic, title, table, examples, tip |
| `content_app/grammar_rules.py` | `seed_grammar_rules()` → `GrammarRule` model |
| `python manage.py seed_content` | Deploy new/changed rules |

Each rule **must** have:

- `summary_ru` — 1–2 sentences (shown in lists)
- `table.rows` — **3 columns**, col3 = **🇷🇺 translation** for every row
- `examples[]` — `{en, ru}` (min 1; needed for practice)
- `tip_ru` — one practical note

## 2. Hub (`rules:hub`)

| Button | Callback | Meaning |
|--------|----------|---------|
| 🎯 Практика · N | `rules:repeat` | Up to 10 rules with exercises |
| 📘 Справочник | `rules:guide` | Browse + mark rules |
| 📗 Мои правила | `rules:mylib` | Personal lists |

## 3. Справочник (`rules:guide`)

| Button | Callback |
|--------|----------|
| 📊 Уровни | `rules:bank` → pick A1…C1 |
| 👀 Знаю? | `rules:survey:menu` |
| 🔍 Поиск | `rules:search` |

### 3.1 Level → category → rules (LOCKED)

**5 разделов на каждом уровне** (A1–C1):

1. **👋 Фразы и общение** (`phrases`)  
2. **⚡ Глаголы и времена** (`verbs`)  
3. **📝 Слова и формы** (`words`) — артикли, сущ., прилаг., местоимения  
4. **🔗 Предлоги и связки** (`links`)  
5. **🧩 Предложение и вопросы** (`syntax`)  

1. **Уровни** → `rules:bank:pick:{level}`  
2. **Раздел** (один из 5)  
3. **Список правил** — tap → detail + 🖼 Spirit card (when uploaded)  
4. Page actions: 🎯 Практика · N, ▶️ По одному, 🟢 / 🎯  

Taxonomy: `learning/grammar/categories.py`. Full syllabus: **`docs/GRAMMAR_RULES_ROADMAP.md`** (~380–420 rules).

### 3.2 Rule detail card (LOCKED display)

Rendered by `learning/grammar/format.format_rule_detail_html`:

```
📘 [A1] Title
📂 Topic · 👋 Общие фразы

Summary (RU)

📋 Таблица
▫️ form
   🇬🇧 example
   🇷🇺 translation

Ещё примеры:
• 🇬🇧 …
  🇷🇺 …

💡 tip
```

On open: **auto 🔊 TTS** (all EN from table + examples). Button **🔊 Слушать примеры** replays.

Actions: ✅ Выучил · 👌 Уже знаю · 🎯 Тренировать

## 4. Personal marks

| Mark | Status | Meaning |
|------|--------|---------|
| ⬜ | — | Not seen |
| 🎯 / ✅ | `learned` | Учить / выучил |
| 🟢 | `known` | Уже знаю |

## 5. Daily plan (future)

Plan block **consumes** rules marked «учить» at user level — same bank, same card format.  
Do not duplicate rule text in plan code; always `get_rule_detail` + `format_rule_detail_html`.

## 6. Key files

| Area | File |
|------|------|
| Bank | `content_app/rules_bank.py` |
| Categories | `learning/grammar/categories.py` |
| Display | `learning/grammar/format.py` |
| Browse | `learning/grammar/service.py` |
| UI | `telegram_app/bot/handlers.py`, `keyboards.py` |

## 7. A1 pilot (2026-08)

9 rules seeded — validate UX before scaling A2+:

| Category | Rules |
|----------|-------|
| Общие фразы | greetings ×2, polite ×2 |
| Глаголы | to be |
| Артикли | a/an |
| Существительные | plural +s |
| Прилагательные | this/that, my/your |

## 8. Smoke checklist

- [ ] A1 → shows category menu (not flat dump)
- [ ] Open rule → table has 🇷🇺 on every row + auto 🔊
- [ ] List page → tap rule title opens detail
- [ ] After `seed_content`, new A1 rules visible on prod

## 9. Full roadmap A1→C1

See **`docs/GRAMMAR_RULES_ROADMAP.md`** — ~380–420 rules, 5 sections per level, Spirit card workflow.
