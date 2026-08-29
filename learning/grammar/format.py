"""Bilingual HTML + TTS text for grammar rule cards (locked display format)."""

from __future__ import annotations

import html
import re
from typing import Any

_EN_RE = re.compile(r'[a-zA-Z]')
_CYR_RE = re.compile(r'[а-яА-ЯёЁ]')
_TIP_QUOTED = re.compile(r'[«""\']([^»""\']+)[»""\']')


def _esc(value: object) -> str:
    return html.escape(str(value))


def _is_english(text: str) -> bool:
    return bool(_EN_RE.search(text or ''))


def _english_from_cell(cell: object) -> str | None:
    """English phrase from a table cell (strip RU half after ·)."""
    text = str(cell).strip()
    if not text or not _is_english(text):
        return None
    if text.endswith('…'):
        return None
    if ' · ' in text:
        en_part = text.split(' · ', 1)[0].strip()
        if _is_english(en_part):
            return en_part
    return text


def _example_column_index(headers: list) -> int:
    """Column that holds the English example on Spirit cards."""
    if not headers:
        return 1
    hdr = [str(h).strip().lower() for h in headers]
    joined = ' '.join(hdr)
    for key in ('пример', 'ответ'):
        for i, h in enumerate(hdr):
            if key in h:
                return i
    if 'фраза' in joined and 'ситуация' not in joined and 'перевод' in joined:
        for i, h in enumerate(hdr):
            if 'фраза' in h:
                return i
    for key in ('фраза',):
        for i, h in enumerate(hdr):
            if key in h:
                return i
    return 1 if len(headers) > 1 else 0


def _tip_english_phrases(tip_ru: str) -> list[str]:
    """English from the orange tip box — quoted phrases + ·-separated lines."""
    if not tip_ru:
        return []
    phrases: list[str] = []
    for match in _TIP_QUOTED.finditer(tip_ru):
        phrase = match.group(1).strip()
        if _is_english(phrase) and phrase not in phrases:
            phrases.append(phrase)
    for part in re.split(r'\s*[·;]\s*', tip_ru):
        cleaned = _TIP_QUOTED.sub('', part).strip()
        if not cleaned or not _is_english(cleaned):
            continue
        latin = len(_EN_RE.findall(cleaned))
        cyr = len(_CYR_RE.findall(cleaned))
        if latin >= 3 and latin >= cyr and cleaned not in phrases:
            phrases.append(cleaned)
    return phrases


def grammar_speak_text(content: dict[str, Any]) -> str | None:
    """Ordered TTS for rule cards: table examples, then tip English — no title/summary/extras."""
    ens: list[str] = []
    table = content.get('table') or {}
    col = _example_column_index(table.get('headers') or [])
    for row in table.get('rows', []):
        cells = list(row)
        if col >= len(cells):
            continue
        phrase = _english_from_cell(cells[col])
        if phrase and phrase not in ens:
            ens.append(phrase)
    for phrase in _tip_english_phrases(content.get('tip_ru') or ''):
        if phrase not in ens:
            ens.append(phrase)
    return '. '.join(ens) if ens else None


def format_rule_examples_html(rule: dict[str, Any]) -> str:
    """Extra examples (+ tip) — shown on «Ещё примеры» tap."""
    parts: list[str] = ['<b>Ещё примеры</b>']
    for ex in rule.get('examples') or []:
        if isinstance(ex, dict):
            en, ru = ex.get('en', ''), ex.get('ru', '')
            if en:
                parts.append(f'• 🇬🇧 {_esc(en)}')
                if ru:
                    parts.append(f'  🇷🇺 {_esc(ru)}')
        else:
            parts.append(f'• {_esc(ex)}')
    tip = rule.get('tip_ru')
    if tip:
        parts.append(f'💡 {_esc(tip)}')
    return '\n\n'.join(parts)


def _table_card_html(headers: list, rows: list) -> str:
    """Compact mobile cards: form | 🇬🇧 example | 🇷🇺 translation (col 3 required)."""
    if not rows:
        return ''
    hdr = headers or ['', '', '']
    legend = ' · '.join(_esc(h) for h in hdr if h)
    parts = ['📋 <b>Таблица</b>']
    if legend:
        parts.append(f'<i>{legend}</i>')
    for row in rows:
        cells = [str(c) for c in row]
        form = cells[0] if cells else ''
        example = cells[1] if len(cells) > 1 else ''
        trans = cells[2] if len(cells) > 2 else ''
        parts.append('')
        if form:
            parts.append(f'▫️ <b>{_esc(form)}</b>')
        if example:
            if _is_english(example):
                parts.append(f'   🇬🇧 {_esc(example)}')
            else:
                parts.append(f'   {_esc(example)}')
        if trans:
            parts.append(f'   🇷🇺 {_esc(trans)}')
        elif example and _is_english(example):
            parts.append('   🇷🇺 <i>—</i>')
    return '\n'.join(parts)


def format_rule_detail_html(rule: dict[str, Any], *, has_card: bool = False) -> str:
    """Rule card body: compact when Spirit image is shown, full table otherwise."""
    from learning.grammar.categories import category_label, category_slug_for_topic

    parts: list[str] = []
    level = (rule.get('level') or '').upper()
    topic = rule.get('topic') or ''
    cat = category_label(category_slug_for_topic(topic))
    title = rule.get('title') or ''

    if has_card:
        topic = rule.get('topic') or ''
        if topic:
            parts.append(f'📂 {_esc(topic)}')
        summary = rule.get('summary_ru') or ''
        if summary:
            parts.append(_esc(summary))
    else:
        parts.append(f'📘 <b>[{level}] {_esc(title)}</b>')
        if topic:
            parts.append(f'📂 {_esc(topic)} · {cat}')
        summary = rule.get('summary_ru') or ''
        if summary:
            parts.append(_esc(summary))
        table = rule.get('table') or {}
        if table.get('rows'):
            parts.append(_table_card_html(table.get('headers', []), table['rows']))

    if not has_card:
        examples = rule.get('examples') or []
        if examples:
            lines = ['<b>Ещё примеры:</b>']
            for ex in examples:
                if isinstance(ex, dict):
                    en, ru = ex.get('en', ''), ex.get('ru', '')
                    if en:
                        lines.append(f'• 🇬🇧 {_esc(en)}')
                        if ru:
                            lines.append(f'  🇷🇺 {_esc(ru)}')
                else:
                    lines.append(f'• {_esc(ex)}')
            parts.append('\n'.join(lines))

        tip = rule.get('tip_ru')
        if tip:
            parts.append(f'💡 {_esc(tip)}')

    return '\n\n'.join(p for p in parts if p) or '…'
