"""Motivation roadmap — journey to the learner's goal CEFR level."""

from __future__ import annotations

from content_app.models import GrammarRule, Lesson
from progress_app.models import UserRule, UserWordProgress
from study_app.models import LessonProgress
from study_app.services.daily_plan import effective_daily_minutes, get_next_episode_lesson
from users_app.models import UserProfile

LEVEL_ORDER = ['a0', 'a1', 'a2', 'b1', 'b2', 'c1', 'c2']
NEXT_LEVEL = {
    'a0': 'A1', 'a1': 'A2', 'a2': 'B1', 'b1': 'B2', 'b2': 'C1', 'c1': 'C2', 'c2': None,
}

# Planned curriculum size (used when DB content is still growing).
PLANNED_LESSONS = {'a1': 12, 'a2': 14, 'b1': 16, 'b2': 18, 'c1': 20, 'c2': 12}
PLANNED_RULES = {'a1': 16, 'a2': 20, 'b1': 24, 'b2': 28, 'c1': 32, 'c2': 20}
MINUTES_PER_EPISODE = 12
MINUTES_PER_RULE = 5

SKILL_FOCUS_RU = {
    'speaking': 'говорение',
    'listening': 'аудирование',
    'reading': 'чтение',
    'writing': 'письмо',
    'grammar': 'грамматика',
    'vocabulary': 'слова',
}


def _norm_level(level: str) -> str:
    lv = (level or 'a1').lower()
    return lv if lv in LEVEL_ORDER else 'a1'


def _level_idx(level: str) -> int:
    return LEVEL_ORDER.index(_norm_level(level))


def _goal_level(profile: UserProfile) -> str:
    if profile.target_cefr_level:
        return profile.target_cefr_level.upper()
    nxt = NEXT_LEVEL.get(_norm_level(profile.cefr_level))
    return nxt or 'C1'


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


def _weeks_range(remaining_minutes: int, *, daily_minutes: int, study_days: int) -> tuple[int, int]:
    weekly = max(1, daily_minutes * max(1, study_days))
    if remaining_minutes <= 0:
        return (1, 2)
    weeks = remaining_minutes / weekly
    low = max(1, int(weeks * 0.85))
    high = max(low + 1, int(weeks * 1.25) + 1)
    return (low, high)


def _months_range(weeks_low: int, weeks_high: int) -> tuple[int, int]:
    m_low = max(1, int(weeks_low / 4.3))
    m_high = max(m_low + 1, int(weeks_high / 4.3) + 1)
    return (m_low, m_high)


def _content_totals(level: str) -> tuple[int, int]:
    lv = level.lower()
    lessons = Lesson.objects.filter(is_published=True, level=lv).count()
    rules = GrammarRule.objects.filter(is_published=True, level=lv).count()
    lessons = max(lessons, PLANNED_LESSONS.get(lv, 10))
    rules = max(rules, PLANNED_RULES.get(lv, 12))
    return lessons, rules


def _remaining_to_goal(profile: UserProfile, current: str, goal: str) -> int:
    cur_i = _level_idx(current)
    goal_i = _level_idx(goal)
    if goal_i <= cur_i:
        goal_i = min(len(LEVEL_ORDER) - 1, cur_i + 1)

    total_minutes = 0
    for i in range(cur_i, goal_i + 1):
        lv = LEVEL_ORDER[i]
        lessons_cap, rules_cap = _content_totals(lv)
        if lv == _norm_level(profile.cefr_level):
            lessons_done = LessonProgress.objects.filter(
                user_id=profile.id,
                lesson_id__in=Lesson.objects.filter(is_published=True, level=lv).values_list('id', flat=True),
                status=LessonProgress.Status.COMPLETED,
            ).count()
            rules_done = UserRule.objects.filter(
                user_id=profile.id,
                rule__level=lv,
                status__in=('learned', 'known'),
            ).count()
            rem_l = max(0, lessons_cap - lessons_done)
            rem_r = max(0, rules_cap - rules_done)
        else:
            rem_l, rem_r = lessons_cap, rules_cap
        total_minutes += rem_l * MINUTES_PER_EPISODE + rem_r * MINUTES_PER_RULE
    return total_minutes


def _journey_map(current: str, goal: str) -> str:
    cur_i = _level_idx(current)
    goal_i = max(_level_idx(goal), cur_i)
    labels = [lv.upper() for lv in LEVEL_ORDER[1:7]]  # A1..C2 display
    idx_map = {lv: i for i, lv in enumerate(LEVEL_ORDER) if lv != 'a0'}

    parts = []
    for label in labels:
        lv = label.lower()
        i = idx_map.get(lv, 0)
        if i < cur_i:
            parts.append(label)
        elif i == cur_i:
            parts.append(f'【{label}】')
        elif i <= goal_i:
            parts.append(label)
        else:
            parts.append('·')
    return ' → '.join(parts)


def build_roadmap(profile: UserProfile) -> dict:
    from gamification_app.models import UserStats

    current = _norm_level(profile.cefr_level)
    step_target = NEXT_LEVEL.get(current)
    goal = _goal_level(profile)
    daily = effective_daily_minutes(profile)
    study_days = profile.study_days_per_week or 5

    stats, _ = UserStats.objects.get_or_create(user=profile)

    lessons_total, rules_total = _content_totals(current)
    lessons_done = LessonProgress.objects.filter(
        user_id=profile.id,
        lesson_id__in=Lesson.objects.filter(is_published=True, level=current).values_list('id', flat=True),
        status=LessonProgress.Status.COMPLETED,
    ).count()
    rules_done = UserRule.objects.filter(
        user_id=profile.id,
        rule__level=current,
        status__in=('learned', 'known'),
    ).count()

    lesson_pct = (lessons_done / lessons_total * 100) if lessons_total else 0
    rule_pct = (rules_done / rules_total * 100) if rules_total else 0
    if lessons_total and rules_total:
        step_pct = round(lesson_pct * 0.6 + rule_pct * 0.4)
    elif lessons_total:
        step_pct = round(lesson_pct)
    else:
        step_pct = round(rule_pct)

    step_remaining = (
        max(0, lessons_total - lessons_done) * MINUTES_PER_EPISODE
        + max(0, rules_total - rules_done) * MINUTES_PER_RULE
    )
    goal_remaining = _remaining_to_goal(profile, current, goal)

    step_weeks = _weeks_range(step_remaining, daily_minutes=daily, study_days=study_days) if step_target else None
    goal_weeks = _weeks_range(goal_remaining, daily_minutes=daily, study_days=study_days)
    goal_months = _months_range(goal_weeks[0], goal_weeks[1])

    next_episode = get_next_episode_lesson(profile)
    focus = profile.skill_focus or profile.weak_skills or []

    return {
        'current_level': current.upper(),
        'step_target_level': step_target,
        'goal_level': goal,
        'step_percent': step_pct,
        'step_bar': _progress_bar(step_pct, 100),
        'lessons_done': lessons_done,
        'lessons_total': lessons_total,
        'lessons_track': _dot_track(lessons_done, lessons_total),
        'rules_done': rules_done,
        'rules_total': rules_total,
        'rules_track': _dot_track(rules_done, rules_total, width=10),
        'words_count': UserWordProgress.objects.filter(user_id=profile.id).count(),
        'daily_minutes': daily,
        'study_days_per_week': study_days,
        'step_weeks_low': step_weeks[0] if step_weeks else None,
        'step_weeks_high': step_weeks[1] if step_weeks else None,
        'goal_weeks_low': goal_weeks[0],
        'goal_weeks_high': goal_weeks[1],
        'goal_months_low': goal_months[0],
        'goal_months_high': goal_months[1],
        'journey_map': _journey_map(current, goal),
        'skill_focus': focus,
        'skill_focus_ru': [SKILL_FOCUS_RU.get(s, s) for s in focus[:4]],
        'next_episode_title': (next_episode.subtitle or next_episode.title) if next_episode else '',
        'xp': stats.xp_total,
        'user_level': stats.level,
        'streak': stats.current_streak,
    }


def format_roadmap_message(roadmap: dict) -> str:
    cur = roadmap['current_level']
    goal = roadmap['goal_level']
    step = roadmap.get('step_target_level')

    lines = [
        '🗺 <b>Карта пути</b>',
        f'📍 Сейчас: <b>{cur}</b>  →  🎯 Цель: <b>{goal}</b>',
        '',
        f'<code>{roadmap["journey_map"]}</code>',
        '',
    ]

    if roadmap.get('skill_focus_ru'):
        lines.append(f'💪 Фокус: {", ".join(roadmap["skill_focus_ru"])}')
        lines.append('')

    if step and step != goal:
        lines.append(f'<b>Ближайшая ступень {cur}→{step}</b>')
        lines.append(f'{roadmap["step_bar"]}  {roadmap["step_percent"]}%')
        if roadmap['lessons_total']:
            lines.append(
                f'📺 {roadmap["lessons_track"]} {roadmap["lessons_done"]}/{roadmap["lessons_total"]} эпизодов'
            )
        if roadmap['rules_total']:
            lines.append(
                f'📖 {roadmap["rules_track"]} {roadmap["rules_done"]}/{roadmap["rules_total"]} правил'
            )
        if roadmap.get('step_weeks_low') is not None:
            lines.append(
                f'⏱ ~{roadmap["step_weeks_low"]}–{roadmap["step_weeks_high"]} нед. до {step}'
            )
        lines.append('')

    lines.append(f'<b>До цели {goal}</b> при {roadmap["daily_minutes"]} мин · '
                   f'{roadmap["study_days_per_week"]} дн/нед:')
    lines.append(
        f'⏱ ~{roadmap["goal_months_low"]}–{roadmap["goal_months_high"]} месяцев '
        f'({roadmap["goal_weeks_low"]}–{roadmap["goal_weeks_high"]} нед.)'
    )

    lines.append('')
    lines.append(
        f'⭐️ XP {roadmap["xp"]}  ·  🔥 {roadmap["streak"]} дн.'
    )

    if roadmap.get('next_episode_title'):
        lines.append('')
        lines.append(f'▶️ Следующий шаг: 📺 {_esc(roadmap["next_episode_title"])}')

    lines.append('')
    lines.append(
        '<i>Оценка по программе в приложении — не гарантия экзамена CEFR. '
        'Контент для C1 растёт — срок уточняется по мере эпизодов.</i>'
    )
    return '\n'.join(lines)


def _esc(value: str) -> str:
    import html
    return html.escape(str(value))
