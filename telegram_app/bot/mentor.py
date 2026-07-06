"""Spirit mentor reactions and episode scenes — keyed by filename."""

from __future__ import annotations

import logging
from typing import TypedDict

from telegram.error import BadRequest

from telegram_app.bot import db

logger = logging.getLogger(__name__)

DEFAULT_MENTOR = 'Spirit'


class _MomentSpec(TypedDict):
    key: str
    compact: bool


# Bot moment → emotion file + display mode (compact circle vs full clip).
SPIRIT_MOMENTS: dict[str, _MomentSpec] = {
    'welcome_back': {'key': 'greeting', 'compact': True},
    'long_absence': {'key': 'sleep', 'compact': True},
    'lesson_resume': {'key': 'pause', 'compact': True},
    'lesson_start': {'key': 'lets_go', 'compact': True},
    'word_review': {'key': 'support', 'compact': True},
    'answer_correct': {'key': 'success', 'compact': True},
    'answer_wrong': {'key': 'think', 'compact': True},
    'grammar_note': {'key': 'explain', 'compact': True},
    'lesson_complete': {'key': 'complete', 'compact': True},
    'lesson_complete_big': {'key': 'applause', 'compact': True},
    'reminder': {'key': 'pause', 'compact': True},
    'goodbye': {'key': 'goodbye', 'compact': True},
    'cliffhanger': {'key': 'surprise', 'compact': True},
}

# Files expected under media/spirit/emotions/ (sync + spirit_status).
EMOTION_KEYS = (
    'greeting', 'sleep', 'lets_go', 'success', 'think', 'explain', 'support',
    'surprise', 'applause', 'complete', 'pause', 'goodbye',
)

# Backward-compatible alias used in a few imports.
REACTION_KEYS = {moment: spec['key'] for moment, spec in SPIRIT_MOMENTS.items()}


async def send_mentor_reaction(
    context,
    chat_id: int,
    moment: str,
    *,
    character: str = DEFAULT_MENTOR,
    compact: bool | None = None,
) -> bool:
    """Send mood clip for a configured moment or a raw file key."""
    spec = SPIRIT_MOMENTS.get(moment)
    if spec:
        key = spec['key']
        use_compact = spec['compact'] if compact is None else compact
    else:
        key = moment
        use_compact = bool(compact)
    return await send_media_by_key(
        context, chat_id, key, character=character, compact=use_compact,
    )


async def send_media_by_key(
    context,
    chat_id: int,
    key: str,
    *,
    character: str = DEFAULT_MENTOR,
    compact: bool = False,
) -> bool:
    clip = await db.get_character_media(character, key)
    if not clip:
        return False

    if compact:
        note_id = clip.get('note_file_id')
        if not note_id:
            return False
        try:
            await context.bot.send_video_note(chat_id, note_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning('mentor note %s/%s failed: %s', character, key, exc)
            return False

    if not clip.get('file_id'):
        return False

    file_id = clip['file_id']
    kind = clip.get('kind', 'animation')
    try:
        if kind == 'image':
            await context.bot.send_photo(chat_id, file_id)
        elif kind == 'video_note':
            await context.bot.send_video_note(chat_id, file_id)
        else:
            try:
                await context.bot.send_animation(chat_id, file_id)
            except BadRequest:
                await context.bot.send_video(chat_id, file_id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning('mentor clip %s/%s failed: %s', character, key, exc)
        return False


def should_show_correct_spirit(user_data: dict) -> bool:
    """Celebrate recovery after a mistake, or every ~3rd correct — not every time."""
    if user_data.get('spirit_after_wrong'):
        return True
    return int(user_data.get('spirit_since_success', 0)) >= 2


def mark_correct_spirit_shown(user_data: dict) -> None:
    user_data['spirit_after_wrong'] = False
    user_data['spirit_since_success'] = 0


def mark_wrong_spirit_shown(user_data: dict) -> None:
    user_data['spirit_after_wrong'] = True
    user_data['spirit_since_success'] = 0


def tick_spirit_exercise(user_data: dict) -> None:
    user_data['spirit_since_success'] = int(user_data.get('spirit_since_success', 0)) + 1
