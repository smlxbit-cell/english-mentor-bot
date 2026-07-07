"""Where in the serial story a learner should enter."""

from __future__ import annotations

from django.utils import timezone

from content_app.models import Lesson
from study_app.models import LessonProgress
from users_app.models import UserProfile

LEVEL_ORDER = ['a0', 'a1', 'a2', 'b1', 'b2', 'c1', 'c2']

# First episode title for learners placed above the A1 funnel.
PLACEMENT_TITLE = {
    'b1': 'Hotel Check-in',
    'b2': 'First Day at Work',
    'c1': 'First Day at Work',
    'c2': 'First Day at Work',
}

# Premium queryset never offers lessons below this level.
ENTRY_LEVEL = {
    'a0': 'a1', 'a1': 'a1', 'a2': 'a2',
    'b1': 'a2', 'b2': 'a2', 'c1': 'b1', 'c2': 'b1',
}


def _norm(level: str) -> str:
    lv = (level or 'a1').lower()
    return lv if lv in LEVEL_ORDER else 'a1'


def level_index(level: str) -> int:
    return LEVEL_ORDER.index(_norm(level))


def entry_level(profile: UserProfile) -> str:
    return ENTRY_LEVEL.get(_norm(profile.cefr_level), 'a1')


def placement_episode_title(profile: UserProfile) -> str | None:
    return PLACEMENT_TITLE.get(_norm(profile.cefr_level))


def apply_story_placement(profile: UserProfile) -> str | None:
    """Skip episodes far below diagnostic level. Returns placement title if applied."""
    if profile.story_placement_applied:
        return None
    title = placement_episode_title(profile)
    if not title:
        profile.story_placement_applied = True
        profile.save(update_fields=['story_placement_applied', 'updated_at'])
        return None

    target = Lesson.objects.filter(title=title, is_published=True).first()
    if not target:
        return None

    now = timezone.now()
    placed = False
    for lesson in Lesson.objects.filter(is_published=True).select_related('unit').order_by(
        'unit__level', 'unit__order', 'order', 'id',
    ):
        if lesson.id == target.id:
            break
        prog, created = LessonProgress.objects.get_or_create(
            user=profile,
            lesson=lesson,
            defaults={'status': LessonProgress.Status.SKIPPED},
        )
        if not created and prog.status == LessonProgress.Status.IN_PROGRESS:
            prog.status = LessonProgress.Status.SKIPPED
            prog.save(update_fields=['status', 'updated_at'])
        placed = True

    profile.story_placement_applied = True
    profile.save(update_fields=['story_placement_applied', 'updated_at'])
    return title if placed else None


def placement_message(title: str, level: str) -> str:
    return (
        f'📍 Твой уровень — <b>{level.upper()}</b>. '
        f'Начинаем историю с эпизода «<b>{title}</b>» — без повторения '
        f'«coffee / tea / please» с нуля.\n\n'
        f'<i>Ранние A1-эпизоды можно пройти позже в списке уроков.</i>'
    )
