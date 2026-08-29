"""Grammar hub: overview, practice queue, personal rule lists."""

from __future__ import annotations

import random
from typing import Any

from content_app.models import GrammarRule
from content_app.rules_bank import RULES_BANK
from progress_app.models import UserRule

from .categories import (
    LEVEL_CATEGORY_ORDER,
    category_button_label,
    category_label,
    category_slug_for_topic,
)
from .nav import CATEGORY_PAGE_HINTS, rule_nav_label

LEVELS = ('a1', 'a2', 'b1', 'b2', 'c1')
PRACTICE_BATCH = 10
SURVEY_BATCH = 10
PAGE_SIZE = 6


def _levels_up_to(level: str) -> list[str]:
    lvl = (level or 'a1').lower()
    if lvl not in LEVELS:
        lvl = 'a1'
    return list(LEVELS[: LEVELS.index(lvl) + 1])


def _rule_has_training(rule: GrammarRule) -> bool:
    examples = rule.examples or []
    return any(
        isinstance(ex, dict) and (ex.get('en') or '').strip()
        for ex in examples
    )


def _user_status_map(profile_id: int, rule_ids: list[int] | None = None) -> dict[int, str]:
    qs = UserRule.objects.filter(user_id=profile_id)
    if rule_ids is not None:
        qs = qs.filter(rule_id__in=rule_ids)
    return {ur.rule_id: ur.status for ur in qs}


def _mark_for_status(status: str) -> str:
    if status in (UserRule.Status.LEARNED, UserRule.Status.KNOWN):
        return '✅'
    return ''


def _rule_browse_item(rule: GrammarRule, user_status: dict[int, str]) -> dict[str, Any]:
    st = user_status.get(rule.id, '')
    return {
        'key': rule.key,
        'title': rule.title,
        'nav_label': rule_nav_label(key=rule.key, title=rule.title, topic=rule.topic),
        'level': rule.level.upper(),
        'topic': rule.topic,
        'summary_ru': (rule.summary_ru or '')[:120],
        'mark': _mark_for_status(st),
        'status': st,
        'has_training': _rule_has_training(rule),
    }


def format_rules_guide_pick_text(
    overview: dict[str, Any],
    *,
    diagnostic_completed: bool = True,
) -> str:
    lvl = overview['user_level'].upper()
    lines = [
        f'📘 <b>Справочник · {lvl}</b>',
        '',
        '<i>Уровни → раздел → правило. Отметь ✅ когда освоил.</i>',
    ]
    if not diagnostic_completed:
        lines.append(
            '\n<i>Пока без теста — показываем правила с вашего гостевого уровня.</i>',
        )
    return '\n'.join(lines)


def format_rules_bank_menu_text(user_level: str) -> str:
    return (
        '📊 <b>Справочник · по уровню</b>\n\n'
        f'Ваш уровень: <b>{user_level.upper()}</b>'
    )


def format_rule_survey_levels_text(user_level: str) -> str:
    lvl = (user_level or 'a1').upper()
    return (
        '👀 <b>Что знаешь?</b>\n\n'
        f'Начните с <b>{lvl}</b> (★) — ваш уровень.\n'
        f'{SURVEY_BATCH} правил подряд: <b>уже знаю</b> или <b>учить</b>.\n'
        'В конце — сразу практика.'
    )


def format_rules_bank_page_text(
    *,
    title: str,
    items: list[dict],
    page: int,
    pages: int,
    total: int,
    category: str | None = None,
) -> str:
    lines = [f'<b>{title}</b>']
    hint = CATEGORY_PAGE_HINTS.get(category or '')
    if hint:
        lines.append(f'<i>{hint}</i>')
    if not items:
        lines.append('')
        lines.append('Правил пока нет.')
        return '\n'.join(lines)
    if pages > 1:
        lines.append(f'<i>Стр. {page + 1}/{pages}</i>')
    return '\n'.join(lines)


def _topics_for_category(level: str, category_slug: str) -> list[str]:
    qs = GrammarRule.objects.filter(
        is_published=True,
        level=level.lower(),
    ).values_list('topic', flat=True).distinct()
    if category_slug == 'other':
        mapped = {
            t for t in qs
            if category_slug_for_topic(t) == 'other'
        }
        return sorted(mapped)
    return sorted(
        t for t in qs
        if category_slug_for_topic(t) == category_slug
    )


def list_rule_categories(
    profile_id: int,
    user_level: str,
    level: str,
    *,
    only_unseen: bool = True,
) -> list[dict[str, Any]]:
    """Sections inside a CEFR level (phrases, verbs, nouns, …)."""
    lvl = level.lower()
    qs = GrammarRule.objects.filter(is_published=True, level=lvl).order_by(
        'order', 'title',
    )
    rule_ids = list(qs.values_list('id', flat=True))
    user_status = _user_status_map(profile_id, rule_ids)
    if only_unseen:
        qs = qs.exclude(
            id__in=[
                rid for rid, st in user_status.items()
                if st in (UserRule.Status.LEARNED, UserRule.Status.KNOWN)
            ],
        )
    counts: dict[str, int] = {}
    for rule in qs:
        slug = category_slug_for_topic(rule.topic)
        counts[slug] = counts.get(slug, 0) + 1
    order = LEVEL_CATEGORY_ORDER.get(lvl, LEVEL_CATEGORY_ORDER['a1'])
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for slug in order:
        if slug in counts:
            items.append({
                'slug': slug,
                'label': category_label(slug),
                'button': category_button_label(slug, counts[slug]),
                'count': counts[slug],
            })
            seen.add(slug)
    for slug, count in sorted(counts.items()):
        if slug not in seen:
            items.append({
                'slug': slug,
                'label': category_label(slug),
                'button': category_button_label(slug, count),
                'count': count,
            })
    return items


def format_rules_category_menu_text(*, level: str) -> str:
    lvl = level.upper()
    return (
        f'📊 <b>{lvl} · разделы</b>\n\n'
        '<i>Выберите раздел. С нуля: 👋 фразы → 📝 местоимения → ⚡ to be.</i>'
    )


def browse_rules_bank(
    profile_id: int,
    user_level: str,
    *,
    level: str | None = None,
    category: str | None = None,
    only_unseen: bool = True,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> dict[str, Any]:
    levels = [level.lower()] if level else _levels_up_to(user_level)
    qs = GrammarRule.objects.filter(is_published=True, level__in=levels).order_by(
        'level', 'order', 'title',
    )
    if category and level:
        topics = _topics_for_category(level, category)
        if topics:
            qs = qs.filter(topic__in=topics)
        elif category != 'other':
            qs = qs.none()
    rule_ids = list(qs.values_list('id', flat=True))
    user_status = _user_status_map(profile_id, rule_ids)
    if only_unseen:
        unseen_ids = [
            rid for rid in rule_ids
            if user_status.get(rid) not in (
                UserRule.Status.LEARNED,
                UserRule.Status.KNOWN,
            )
        ]
        qs = qs.filter(id__in=unseen_ids)
    total = qs.count()
    pages = max(1, (total + page_size - 1) // page_size)
    page = max(0, min(page, pages - 1))
    page_rules = list(qs[page * page_size:(page + 1) * page_size])
    return {
        'items': [_rule_browse_item(r, user_status) for r in page_rules],
        'total': total,
        'page': page,
        'pages': pages,
        'level': level,
        'category': category,
    }


def pick_rule_survey_batch(
    profile_id: int,
    level: str,
    *,
    limit: int = SURVEY_BATCH,
) -> list[dict]:
    data = browse_rules_bank(
        profile_id, level, level=level, only_unseen=True, page=0, page_size=limit,
    )
    return data['items'][:limit]


def search_rules(
    profile_id: int,
    user_level: str,
    query: str,
    *,
    limit: int = 8,
) -> list[dict]:
    from django.db.models import Q

    q = (query or '').strip()
    if len(q) < 2:
        return []
    allowed = _levels_up_to(user_level)
    hits = GrammarRule.objects.filter(
        is_published=True,
        level__in=allowed,
    ).filter(
        Q(title__icontains=q)
        | Q(summary_ru__icontains=q)
        | Q(topic__icontains=q)
        | Q(key__icontains=q.replace(' ', '-'))
    ).order_by('level', 'order', 'title')[:limit * 2]
    nav_keys = [
        r['key'] for r in RULES_BANK
        if q.lower() in (r.get('nav_ru') or '').lower()
    ]
    if nav_keys:
        hits = list(hits) + list(
            GrammarRule.objects.filter(
                is_published=True,
                level__in=allowed,
                key__in=nav_keys,
            ).order_by('level', 'order', 'title'),
        )
        seen: set[str] = set()
        deduped = []
        for rule in hits:
            if rule.key in seen:
                continue
            seen.add(rule.key)
            deduped.append(rule)
        hits = deduped[:limit]
    else:
        hits = list(hits[:limit])
    user_status = _user_status_map(profile_id, [r.id for r in hits])
    return [_rule_browse_item(r, user_status) for r in hits]


def mark_rules_bulk(profile_id: int, rule_keys: list[str], status: str) -> int:
    if status == 'known':
        status = UserRule.Status.LEARNED
    from content_app.models import GrammarRule

    rules = {
        r.key: r
        for r in GrammarRule.objects.filter(key__in=rule_keys, is_published=True)
    }
    n = 0
    for key in rule_keys:
        rule = rules.get(key)
        if not rule:
            continue
        ur, _ = UserRule.objects.get_or_create(
            user_id=profile_id,
            rule=rule,
            defaults={'status': status},
        )
        if ur.status != status:
            ur.status = status
            ur.save(update_fields=['status', 'updated_at'])
        n += 1
    return n


def list_my_rule_topic_counts(profile_id: int, user_level: str) -> list[tuple[str, int]]:
    allowed = _levels_up_to(user_level)
    counts: dict[str, int] = {}
    for ur in UserRule.objects.filter(
        user_id=profile_id,
        status__in=(UserRule.Status.LEARNED, UserRule.Status.KNOWN),
        rule__is_published=True,
        rule__level__in=allowed,
    ).select_related('rule'):
        topic = ur.rule.topic or 'Общее'
        counts[topic] = counts.get(topic, 0) + 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


def list_my_rules_filtered(
    profile_id: int,
    user_level: str,
    *,
    status: str | None = None,
    level: str | None = None,
    topic: str | None = None,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> dict[str, Any]:
    allowed = _levels_up_to(user_level)
    qs = UserRule.objects.filter(
        user_id=profile_id,
        status__in=(UserRule.Status.LEARNED, UserRule.Status.KNOWN),
        rule__is_published=True,
        rule__level__in=allowed,
    ).select_related('rule')
    if status:
        qs = qs.filter(status=status)
    if level:
        qs = qs.filter(rule__level=level.lower())
    if topic:
        qs = qs.filter(rule__topic=topic)
    qs = qs.order_by('rule__level', 'rule__order', 'rule__title')
    total = qs.count()
    pages = max(1, (total + page_size - 1) // page_size)
    page = max(0, min(page, pages - 1))
    items = [
        {
            'key': ur.rule.key,
            'title': ur.rule.title,
            'level': ur.rule.level.upper(),
            'topic': ur.rule.topic,
            'status': ur.status,
            'mark': _mark_for_status(ur.status),
        }
        for ur in qs[page * page_size:(page + 1) * page_size]
    ]
    return {
        'items': items,
        'total': total,
        'page': page,
        'pages': pages,
        'status': status,
        'level': level,
        'topic': topic,
    }


def format_my_rules_stats_line(summary: dict[str, Any]) -> str:
    in_lib = summary['learned'] + summary.get('known', 0)
    return f'✅ в библиотеке <b>{in_lib}</b>'


def get_rules_overview(profile_id: int, user_level: str) -> dict[str, Any]:
    allowed = _levels_up_to(user_level)
    rules = list(
        GrammarRule.objects.filter(is_published=True, level__in=allowed)
        .order_by('level', 'order', 'id'),
    )
    user_status = {
        ur.rule_id: ur.status
        for ur in UserRule.objects.filter(user_id=profile_id, rule__in=rules)
    }
    topics: set[str] = set()
    learned = known = new = 0
    trainable_new: list[str] = []
    trainable_all: list[str] = []
    for rule in rules:
        topics.add(rule.topic)
        st = user_status.get(rule.id, '')
        if st == UserRule.Status.LEARNED:
            learned += 1
        elif st == UserRule.Status.KNOWN:
            known += 1
        else:
            new += 1
        if not _rule_has_training(rule):
            continue
        trainable_all.append(rule.key)
        if st not in (UserRule.Status.LEARNED, UserRule.Status.KNOWN):
            trainable_new.append(rule.key)

    practice_pool = trainable_new or trainable_all
    practice_count = min(PRACTICE_BATCH, len(practice_pool))

    return {
        'user_level': user_level.lower(),
        'total': len(rules),
        'learned': learned,
        'known': known,
        'new': new,
        'topics_count': len(topics),
        'practice_count': practice_count,
        'practice_pool_size': len(practice_pool),
    }


def format_rules_hub_text(
    overview: dict[str, Any],
    *,
    diagnostic_completed: bool = True,
) -> str:
    user_lvl = overview['user_level'].upper()
    lines = [
        '🎓 <b>Грамматика</b>',
        '',
    ]
    if diagnostic_completed:
        lines.append(f'Твой уровень: <b>{user_lvl}</b> · по результатам теста')
    else:
        lines.append(
            f'Пока без теста · правила с <b>{user_lvl}</b> '
            f'<i>(уточни уровень — подберём точнее)</i>',
        )
    in_library = overview['learned'] + overview['known']
    lines.extend([
        '',
        f'✅ в библиотеке <b>{in_library}</b> · '
        f'📖 новых <b>{overview["new"]}</b>',
        f'Разделов: {overview["topics_count"]} · правил: {overview["total"]}',
        '',
        f'🎯 <b>Практика</b> — до {overview["practice_count"]} правил',
    ])
    return '\n'.join(lines)


def pick_practice_rule_keys(
    profile_id: int,
    user_level: str,
    *,
    limit: int = PRACTICE_BATCH,
) -> list[str]:
    overview = get_rules_overview(profile_id, user_level)
    allowed = _levels_up_to(user_level)
    user_status = {
        ur.rule_id: ur.status
        for ur in UserRule.objects.filter(user_id=profile_id).select_related('rule')
    }
    fresh: list[str] = []
    review: list[str] = []
    for rule in GrammarRule.objects.filter(is_published=True, level__in=allowed):
        if not _rule_has_training(rule):
            continue
        st = user_status.get(rule.id, '')
        if st in (UserRule.Status.LEARNED, UserRule.Status.KNOWN):
            review.append(rule.key)
        else:
            fresh.append(rule.key)
    pool = fresh or review
    if not pool:
        return []
    random.shuffle(pool)
    return pool[:limit]


def get_my_rules_summary(profile_id: int, user_level: str) -> dict[str, Any]:
    allowed = _levels_up_to(user_level)
    qs = UserRule.objects.filter(
        user_id=profile_id,
        rule__is_published=True,
        rule__level__in=allowed,
    )
    learned = qs.filter(status=UserRule.Status.LEARNED).count()
    known = qs.filter(status=UserRule.Status.KNOWN).count()
    return {
        'learned': learned,
        'known': known,
        'total': learned + known,
    }


def format_my_rules_hub(summary: dict[str, Any]) -> str:
    if summary['total'] == 0:
        return (
            '📗 <b>Мои правила</b>\n\n'
            'Пока пусто. 📘 <b>Справочник</b> → «👀 Знаю?» '
            'или уровень — отметь «🟢 Уже знаю» / «🎯 Учить».'
        )
    return (
        '📗 <b>Мои правила</b>\n\n'
        + format_my_rules_stats_line(summary)
    )


def list_my_rules(
    profile_id: int,
    user_level: str,
    *,
    status: str,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> dict[str, Any]:
    allowed = _levels_up_to(user_level)
    qs = (
        UserRule.objects.filter(
            user_id=profile_id,
            status=status,
            rule__is_published=True,
            rule__level__in=allowed,
        )
        .select_related('rule')
        .order_by('rule__level', 'rule__order', 'rule__title')
    )
    total = qs.count()
    pages = max(1, (total + page_size - 1) // page_size)
    page = max(0, min(page, pages - 1))
    items = [
        {
            'key': ur.rule.key,
            'title': ur.rule.title,
            'level': ur.rule.level.upper(),
            'topic': ur.rule.topic,
            'status': ur.status,
        }
        for ur in qs[page * page_size:(page + 1) * page_size]
    ]
    title = '✅ Выучил' if status == UserRule.Status.LEARNED else '🟢 Уже знаю'
    return {
        'title': title,
        'items': items,
        'page': page,
        'pages': pages,
        'total': total,
        'status': status,
    }


def format_rule_list_page(data: dict[str, Any]) -> str:
    lines = [f'<b>{data["title"]}</b>', '']
    if not data['items']:
        lines.append('Здесь пока пусто.')
        return '\n'.join(lines)
    for item in data['items']:
        lines.append(
            f'[{item["level"]}] <b>{item["title"]}</b>\n'
            f'   <i>{item["topic"]}</i>',
        )
    lines.extend(['', f'Стр. {data["page"] + 1}/{data["pages"]} · всего {data["total"]}'])
    return '\n'.join(lines)
