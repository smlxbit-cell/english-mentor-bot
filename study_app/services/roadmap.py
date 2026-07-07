"""Motivation roadmap — realistic ETA and path to the next CEFR level."""

from __future__ import annotations

from content_app.models import GrammarRule, Lesson
from progress_app.models import UserRule, UserWordProgress
from study_app.models import LessonProgress
from study_app.services.daily_plan import effective_daily_minutes, get_next_episode_lesson
from users_app.models import UserProfile

LEVEL_ORDER = ['a0', 'a1', 'a2', 'b1', 'b2', 'c1', 'c2']
NEXT_LEVEL = {
    'a0': 'A1',
    'a1': 'A2',
    'a2': 'B1',
    'b1': 'B2',
    'b2': 'C1',
    'c1': 'C2',
    'c2': None,
}

# Heuristic minutes per unit (planning estimate, not a promise).
MINUTES_PER_EPISODE = 12
MINUTES_PER_RULE = 5


def _norm_level(level: str) -> str:
    lv = (level or 'a1').lower()
    return lv if lv in LEVEL_ORDER else 'a1'


def _progress_bar(filled: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return '░' * width
    n = round(filled / total * width)
    return '━' * n + '░' * (width - n)


def _dot_track(done: int, total: int, width: int = 8) -> str:
    if total <= 0:
        return '○' * min(width, 4)
    filled = round(done / total * width)
    return '●' * filled + '○' * (width - filled)


def _weeks_range(
    remaining_minutes: int,
    *,
    daily_minutes: int,
    study_days: int,
) -> tuple[int, int] | None:
    weekly = max(1, daily_minutes * max(1, study_days))
    if remaining_minutes <= 0:
        return (1, 2)
    weeks = remaining_minutes / weekly
    low = max(1, int(weeks * 0.85))
    high = max(low + 1, int(weeks * 1.25) + 1)
    return (low, high)


def build_roadmap(profile: UserProfile) -> dict:
    """Roadmap dict for progress screen and reminders."""
    from gamification_app.models import UserStats

    current = _norm_level(profile.cefr_level)
    target = NEXT_LEVEL.get(current)
    daily = effective_daily_minutes(profile)
    study_days = profile.study_days_per_week or 5

    stats, _ = UserStats.objects.get_or_create(user=profile)

    lesson_ids_at_level = list(
        Lesson.objects.filter(is_published=True, level=current).values_list('id', flat=True)
    )
    lessons_total = len(lesson_ids_at_level)
    lessons_done = LessonProgress.objects.filter(
        user_id=profile.id,
        lesson_id__in=lesson_ids_at_level,
        status=LessonProgress.Status.COMPLETED,
    ).count()

    rules_qs = GrammarRule.objects.filter(is_published=True, level=current)
    rules_total = rules_qs.count()
    rule_ids_at_level = list(rules_qs.values_list('id', flat=True))
    rules_done = UserRule.objects.filter(
        user_id=profile.id,
        rule_id__in=rule_ids_at_level,
        status__in=('learned', 'known'),
    ).count()

    words_count = UserWordProgress.objects.filter(user_id=profile.id).count()

    lesson_pct = (lessons_done / lessons_total * 100) if lessons_total else 100
    rule_pct = (rules_done / rules_total * 100) if rules_total else 100
    if lessons_total and rules_total:
        overall_pct = round(lesson_pct * 0.6 + rule_pct * 0.4)
    elif lessons_total:
        overall_pct = round(lesson_pct)
    elif rules_total:
        overall_pct = round(rule_pct)
    else:
        overall_pct = 0

    remaining_minutes = (
        max(0, lessons_total - lessons_done) * MINUTES_PER_EPISODE
        + max(0, rules_total - rules_done) * MINUTES_PER_RULE
    )
    weeks = _weeks_range(
        remaining_minutes,
        daily_minutes=daily,
        study_days=study_days,
    ) if target else None

    next_episode = get_next_episode_lesson(profile)
    next_episode_title = ''
    if next_episode:
        next_episode_title = next_episode.subtitle or next_episode.title

    learned_rule_ids = set(
        UserRule.objects.filter(
            user_id=profile.id,
            rule_id__in=rule_ids_at_level,
            status__in=('learned', 'known'),
        ).values_list('rule_id', flat=True)
    )
    upcoming_rules = list(
        rules_qs.exclude(id__in=learned_rule_ids).order_by('order', 'title')[:3].values(
            'title', 'level',
        )
    )

    # Journey map: nodes for current level episodes + arrow to target
    map_nodes = []
    if lessons_total:
        for i in range(min(lessons_total, 6)):
            map_nodes.append('●' if i < lessons_done else '○')
        if lessons_total > 6:
            map_nodes.append('…')
    map_line = ' '.join(map_nodes) if map_nodes else '○'

    return {
        'current_level': current.upper(),
        'target_level': target,
        'overall_percent': overall_pct,
        'overall_bar': _progress_bar(overall_pct, 100),
        'lessons_done': lessons_done,
        'lessons_total': lessons_total,
        'lessons_track': _dot_track(lessons_done, lessons_total),
        'rules_done': rules_done,
        'rules_total': rules_total,
        'rules_track': _dot_track(rules_done, rules_total, width=10),
        'words_count': words_count,
        'daily_minutes': daily,
        'study_days_per_week': study_days,
        'weeks_low': weeks[0] if weeks else None,
        'weeks_high': weeks[1] if weeks else None,
        'remaining_minutes': remaining_minutes,
        'next_episode_title': next_episode_title,
        'upcoming_rules': upcoming_rules,
        'map_line': map_line,
        'xp': stats.xp_total,
        'user_level': stats.level,
        'streak': stats.current_streak,
        'longest_streak': stats.longest_streak,
        'at_max_level': target is None,
    }


def format_roadmap_message(roadmap: dict) -> str:
    """Telegram HTML message for 📊 Прогресс."""
    cur = roadmap['current_level']
    tgt = roadmap.get('target_level')
    pct = roadmap['overall_percent']
    bar = roadmap['overall_bar']

    lines = [
        f'🗺 <b>Карта пути</b> · {cur}' + (f' → {tgt}' if tgt else ''),
        '',
        f'{bar}  <b>{pct}%</b> до следующего уровня',
        '',
    ]

    if roadmap['lessons_total']:
        lines.append(
            f'📺 Эпизоды:  {roadmap["lessons_track"]}  '
            f'{roadmap["lessons_done"]}/{roadmap["lessons_total"]}'
        )
    if roadmap['rules_total']:
        lines.append(
            f'📖 Правила:  {roadmap["rules_track"]}  '
            f'{roadmap["rules_done"]}/{roadmap["rules_total"]}'
        )
    if roadmap['words_count']:
        lines.append(f'🗂 Словарь: {roadmap["words_count"]} слов')

    lines.append('')
    lines.append(
        f'⭐️ XP: {roadmap["xp"]}  ·  🎮 ур. {roadmap["user_level"]}  ·  '
        f'🔥 {roadmap["streak"]} дн.'
    )

    if tgt and roadmap.get('weeks_low') is not None:
        wl, wh = roadmap['weeks_low'], roadmap['weeks_high']
        lines.append('')
        lines.append(f'⏱ <b>До {tgt}</b> при твоём темпе:')
        lines.append(f'   ~{wl}–{wh} недель')
        lines.append(
            f'   ({roadmap["daily_minutes"]} мин · '
            f'{roadmap["study_days_per_week"]} дн/нед)'
        )
    elif roadmap.get('at_max_level'):
        lines.append('')
        lines.append('🏆 Ты на верхней отметке карты — продолжаем углублять!')

    if roadmap.get('next_episode_title'):
        lines.append('')
        lines.append('<b>▶️ Следующий шаг</b>')
        lines.append(f'   📺 {_esc(roadmap["next_episode_title"])}')

    upcoming = roadmap.get('upcoming_rules') or []
    if upcoming:
        lines.append('')
        lines.append('<b>🔓 Скоро в библиотеке</b>')
        for rule in upcoming[:3]:
            lines.append(f'   • {_esc(rule["title"])}')

    if roadmap.get('map_line') and tgt:
        lines.append('')
        lines.append(f'<code>{cur} {roadmap["map_line"]} {tgt}</code>')

    lines.append('')
    lines.append(
        '<i>Оценка по эпизодам и правилам в приложении — '
        'не гарантия экзамена CEFR.</i>'
    )
    return '\n'.join(lines)


def _esc(value: str) -> str:
    import html
    return html.escape(str(value))
