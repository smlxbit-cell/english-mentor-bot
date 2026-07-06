"""Seed GrammarRule rows from the rules bank + lesson curriculum."""

from __future__ import annotations

from content_app.curriculum import CURRICULUM
from content_app.models import GrammarRule, LessonStep
from content_app.rules_bank import RULES_BANK


def _upsert_rule(key: str, defaults: dict) -> None:
    GrammarRule.objects.update_or_create(key=key, defaults=defaults)


def _rule_defaults_from_bank(rule: dict) -> dict:
    return {
        'topic': rule['topic'],
        'title': rule['title'],
        'level': rule['level'],
        'summary_ru': rule.get('summary_ru', ''),
        'table': rule.get('table', {}),
        'examples': rule.get('examples', []),
        'tip_ru': rule.get('tip_ru', ''),
        'order': rule.get('order', 0),
        'is_published': True,
    }


def _rule_defaults_from_step(step: dict, level: str) -> dict:
    content = step.get('content') or {}
    return {
        'topic': (step.get('title') or content.get('rule_key', ''))[:100],
        'title': step.get('title') or content.get('rule_key', ''),
        'level': level,
        'summary_ru': content.get('rule_ru', ''),
        'table': content.get('table', {}),
        'examples': content.get('examples', []),
        'tip_ru': content.get('tip_ru', ''),
        'is_published': True,
    }


def seed_grammar_rules() -> int:
    """Upsert rules bank, then overlay episode-authored grammar steps."""
    count = 0
    for rule in RULES_BANK:
        _upsert_rule(rule['key'], _rule_defaults_from_bank(rule))
        count += 1

    seen: set[str] = {r['key'] for r in RULES_BANK}

    for block in CURRICULUM:
        level = block['unit']['level']
        for lesson_data in block['lessons']:
            for step in lesson_data.get('steps', []):
                if step.get('type') != 'grammar_note':
                    continue
                content = step.get('content') or {}
                key = content.get('rule_key')
                if not key:
                    continue
                defaults = _rule_defaults_from_step(step, level)
                if key in seen:
                    # Keep bank order/topic; refresh lesson-authored text.
                    existing = GrammarRule.objects.filter(key=key).first()
                    if existing:
                        defaults['order'] = existing.order
                        defaults['topic'] = existing.topic
                else:
                    defaults['order'] = count + 1
                    count += 1
                    seen.add(key)
                _upsert_rule(key, defaults)

    for step in LessonStep.objects.filter(step_type='grammar_note'):
        content = step.content or {}
        key = content.get('rule_key')
        if not key or key in seen:
            continue
        seen.add(key)
        count += 1
        _upsert_rule(
            key,
            {
                'topic': (step.title or key)[:100],
                'title': step.title or key,
                'level': step.lesson.level,
                'summary_ru': content.get('rule_ru', ''),
                'table': content.get('table', {}),
                'examples': content.get('examples', []),
                'tip_ru': content.get('tip_ru', ''),
                'order': count,
                'is_published': True,
            },
        )

    return GrammarRule.objects.filter(is_published=True).count()
