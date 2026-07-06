"""Telegram bot: onboarding, adaptive diagnostic, interactive lessons
(with media, voice and AI checking), gamification and the 390 ₽ paywall.

State for the current flow lives in context.user_data (in-memory, single polling
process). DB access goes through .db (async wrappers). AI/STT go through ai_app.
"""

from __future__ import annotations

import difflib
import html
import io
import logging
import random
import re

from django.conf import settings
from telegram import BotCommand, LabeledPrice, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from ai_app.services import (
    AnswerChecker,
    ChatMessage,
    DialoguePartner,
    explain_grammar,
    generate_practice,
    normalize,
    score_speaking,
    score_word_review,
)
from ai_app.speech import get_stt_provider
from ai_app.tts import get_tts_provider

from . import db, keyboards
from .mentor import (
    mark_correct_spirit_shown,
    mark_wrong_spirit_shown,
    send_media_by_key,
    send_mentor_reaction,
    should_show_correct_spirit,
    tick_spirit_exercise,
)

logger = logging.getLogger(__name__)

checker = AnswerChecker()
partner = DialoguePartner()

MAX_DIAGNOSTIC_QUESTIONS = 6

# Open-ended exercise types where voice answers are useful (STT → same checker).
VOICE_EXERCISE_TYPES = frozenset({
    'fill_gap', 'short_answer', 'translation_ru_en', 'translation_en_ru',
    'writing', 'word_order', 'auto_exact',
})

# item_type -> deterministic exercise_type used by the checker
_DIAG_CHECK_TYPE = {
    'multiple_choice': 'multiple_choice',
    'listening': 'multiple_choice',
    'fill_gap': 'fill_gap',
    'translation_ru_en': 'translation_ru_en',
}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

async def _ensure_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
    profile = await db.get_or_create_profile(update.effective_user)
    context.user_data['profile_id'] = profile['id']
    context.user_data['user_key'] = str(update.effective_user.id)
    context.user_data['sphere_en'] = profile.get('sphere_en', '')
    return profile


def _chat_id(update: Update) -> int:
    if update.callback_query:
        return update.callback_query.message.chat_id
    return update.effective_chat.id


async def _send(context, chat_id, text, reply_markup=None, parse_mode=None):
    await context.bot.send_message(
        chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode,
    )


def _esc(value) -> str:
    return html.escape(str(value))


def _step_uses_html(step: dict) -> bool:
    blob = (step.get('text') or '') + (step.get('title') or '')
    return bool(re.search(r'</?[bi]>|<code>', blob))


def _table_html(headers: list, rows: list) -> str:
    """Card-style table readable on mobile (Telegram HTML has no <table> tag)."""
    if not rows:
        return ''
    parts = ['📋 <b>Таблица</b>']
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
    return '\n'.join(parts)


def _grammar_speak_text(content: dict) -> str | None:
    """Collect all English phrases from a grammar rule for TTS."""
    ens: list[str] = []
    table = content.get('table') or {}
    for row in table.get('rows', []):
        for i, cell in enumerate(row):
            cell = str(cell).strip()
            if not cell or not _is_english(cell):
                continue
            # Prefer example column; skip bare patterns with ellipsis only.
            if i == 0 and cell.endswith('…'):
                continue
            if cell not in ens:
                ens.append(cell)
    for ex in content.get('examples') or []:
        if isinstance(ex, dict) and ex.get('en'):
            ens.append(ex['en'])
        elif isinstance(ex, str) and _is_english(ex):
            ens.append(ex)
    return '. '.join(ens) if ens else None


def _grammar_html(step: dict) -> str:
    """Build a bilingual grammar message (rule + table + examples + tip) as HTML."""
    content = step.get('content') or {}
    parts = []

    title = step.get('title') or content.get('title')
    if title:
        parts.append(f'📘 <b>{_esc(title)}</b>')

    rule = content.get('rule_ru') or content.get('rule')
    if rule:
        parts.append(_esc(rule))

    table = content.get('table') or {}
    if table.get('rows'):
        parts.append(_table_html(table.get('headers', []), table['rows']))

    examples = content.get('examples') or []
    if examples:
        lines = ['<b>Примеры:</b>']
        for ex in examples:
            if isinstance(ex, dict):
                en, ru = ex.get('en', ''), ex.get('ru', '')
                lines.append(f'• {_esc(en)}' + (f' — {_esc(ru)}' if ru else ''))
            else:
                lines.append(f'• {_esc(ex)}')
        parts.append('\n'.join(lines))

    tip = content.get('tip_ru')
    if tip:
        parts.append(f'💡 {_esc(tip)}')

    return '\n\n'.join(p for p in parts if p) or '…'


async def _send_media(context, chat_id, media: dict | None):
    """Best-effort media delivery. Never breaks the lesson if media fails."""
    if not media:
        return
    ref = media.get('telegram_file_id') or media.get('source_url') or ''
    fileobj = None
    if not ref and media.get('file'):
        import os
        path = os.path.join(settings.MEDIA_ROOT, media['file'])
        if os.path.exists(path):
            fileobj = open(path, 'rb')  # noqa: SIM115
    target = fileobj or ref
    if not target:
        return
    mtype = media.get('media_type')
    try:
        if mtype == 'image':
            await context.bot.send_photo(chat_id, target)
        elif mtype in ('gif', 'animation'):
            await context.bot.send_animation(chat_id, target)
        elif mtype == 'audio':
            await context.bot.send_audio(chat_id, target)
        elif mtype == 'video':
            await context.bot.send_video(chat_id, target)
        elif mtype == 'video_note':
            await context.bot.send_video_note(chat_id, target)
        else:
            await context.bot.send_document(chat_id, target)
    except Exception as exc:  # noqa: BLE001
        logger.warning('media send failed: %s', exc)
    finally:
        if fileobj:
            fileobj.close()


async def _send_character_turn(
    context,
    chat_id: int,
    *,
    character: dict,
    text: str,
    reply_markup=None,
    show_video: bool = True,
) -> None:
    """Character reply: optional circular video + text + TTS hook."""
    context.user_data['tts_text'] = text
    video_id = character.get('video_note_file_id', '')
    if show_video and video_id:
        try:
            await context.bot.send_video_note(chat_id, video_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning('video_note send failed: %s', exc)
    who = character.get('name', 'Emma')
    await _send(
        context, chat_id,
        f'💬 <b>{_esc(who)}</b>: {_esc(text)}',
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )


async def _send_tts(context, chat_id, text: str) -> bool:
    """Voice English `text` via TTS (edge-tts by default). Best-effort."""
    text = (text or '').strip()
    if not text or not settings.TTS_ENABLED:
        return False
    try:
        provider = get_tts_provider()
        result = await provider.synthesize(text)
    except Exception as exc:  # noqa: BLE001
        logger.warning('tts failed: %s', exc)
        return False
    if not result.ok or not result.audio:
        return False

    bio = io.BytesIO(result.audio)
    bio.name = f'speech.{result.fmt}'
    try:
        if result.fmt == 'ogg':
            await context.bot.send_voice(chat_id, bio)
        else:
            await context.bot.send_audio(chat_id, bio, title='🔊 English')
    except Exception as exc:  # noqa: BLE001
        logger.warning('tts send failed: %s', exc)
        return False
    return True


def _voice_allowed(context) -> bool:
    """True when the current flow accepts a Telegram voice message."""
    mode = context.user_data.get('mode')
    expect = context.user_data.get('expect')
    if mode in ('diagnostic', 'dialogue', 'tutor', 'review'):
        return True
    if mode == 'practice' and context.user_data.get('practice_expect') == 'text':
        return True
    if mode == 'lesson' and expect in ('ex_voice', 'ex_text_or_voice'):
        return True
    return False


def _stt_langs_for_context(context) -> list[str]:
    """Language(s) to try for speech recognition."""
    mode = context.user_data.get('mode')
    if mode == 'tutor':
        return ['ru-RU', 'en-US']
    if mode == 'review':
        return ['en-US']
    if mode == 'lesson':
        return ['en-US']
    if mode == 'dialogue':
        return ['en-US']
    return ['en-US']


def _exercise_has_hint(content: dict) -> bool:
    return bool(
        content.get('hint_detail_ru') or content.get('rule_key') or content.get('hint_ru')
    )


def _stt_short_utterance(context) -> bool:
    """Single-word answers (SRS, fill_gap) need tuned STT + fuzzy match."""
    if context.user_data.get('mode') == 'review':
        return True
    step = context.user_data.get('current_step') or {}
    content = step.get('content') or {}
    if content.get('exercise_type') == 'fill_gap':
        correct = content.get('correct')
        if isinstance(correct, (list, tuple)):
            items = [str(c).strip() for c in correct if str(c).strip()]
        else:
            items = [str(correct).strip()] if correct else []
        if items and all(' ' not in normalize(i) for i in items):
            return True
    return False


async def _transcribe_voice(update: Update, context, *, langs: list[str] | None = None) -> str:
    """Download voice from Telegram and transcribe via STT. Returns '' on failure."""
    langs = langs or _stt_langs_for_context(context)
    short = _stt_short_utterance(context)
    try:
        tg_file = await context.bot.get_file(update.message.voice.file_id)
        audio = bytes(await tg_file.download_as_bytearray())
        stt = get_stt_provider()
    except Exception as exc:  # noqa: BLE001
        logger.warning('voice download failed: %s', exc)
        return ''

    for lang in langs:
        try:
            transcript = await stt.transcribe(audio, lang=lang, short_utterance=short)
            text = (transcript.text or '').strip()
            if text:
                return text
        except Exception as exc:  # noqa: BLE001
            logger.warning('STT failed (%s): %s', lang, exc)
    return ''


def _exercise_accepts_voice(content: dict, etype: str) -> bool:
    if content.get('accept_voice') is False:
        return False
    if content.get('accept_voice') is True:
        return True
    return etype in VOICE_EXERCISE_TYPES


def _is_english(text: str | None) -> bool:
    """True if `text` is predominantly English (so we can safely voice it)."""
    if not text:
        return False
    latin = len(re.findall(r'[A-Za-z]', text))
    cyrillic = len(re.findall(r'[А-Яа-яЁё]', text))
    return latin >= 3 and latin >= cyrillic


def _speak_text_for_step(step: dict) -> str | None:
    """Return the English text to voice for a step, or None if nothing to say.

    Only genuinely English content is returned; Russian narration (hooks, most
    story text) is skipped so we never mispronounce it with an English voice.
    """
    if not step:
        return None
    content = step.get('content') or {}
    if content.get('speak_en'):
        return content['speak_en']
    if content.get('speak'):
        return content['speak']

    stype = step.get('step_type')

    if stype == 'vocabulary' and content.get('words'):
        chunks = []
        for w in content['words']:
            en = w.get('en', '')
            if not en:
                continue
            chunks.append(en if not w.get('example') else f'{en}. {w["example"]}')
        return '. '.join(chunks) or None

    if stype == 'speaking':
        return content.get('target') or None

    if stype == 'dialogue' and content.get('lines'):
        parts = [ln.get('text', '') for ln in content['lines'] if ln.get('text')]
        english = [p for p in parts if _is_english(p)]
        return '. '.join(english) or None

    if stype == 'grammar_note':
        return _grammar_speak_text(content)

    # Generic: voice the step's English text/title if it looks English.
    for candidate in (step.get('text'), step.get('title')):
        if _is_english(candidate):
            return candidate
    return None


# --------------------------------------------------------------------------- #
# /start & menu
# --------------------------------------------------------------------------- #

LONG_ABSENCE_DAYS = 7


def _days_ru(n: int) -> str:
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return f'{n} день'
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f'{n} дня'
    return f'{n} дней'


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    name = profile['first_name'] or 'друг'
    chat_id = _chat_id(update)

    if not profile['diagnostic_completed']:
        await send_mentor_reaction(context, chat_id, 'welcome_back')
        await _send(
            context, chat_id,
            f'Привет, {name}! 👋\n\n'
            'Я — English Mentor. Помогу учить английский маленькими шагами: '
            'истории, диалоги, игры и живая практика с проверкой ответов.\n\n'
            'Сначала пройдём короткую диагностику уровня — это бесплатно и займёт '
            '2–3 минуты. Можно отвечать текстом или голосом 🎙️',
            reply_markup=keyboards.start_diagnostic_kb(),
        )
        return

    from django.utils import timezone as dj_tz
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    prev = profile.get('previous_last_seen')
    days_away = (dj_tz.now() - prev).days if prev else 0
    unfinished = await db.get_in_progress_lesson(profile['id'])

    if days_away >= LONG_ABSENCE_DAYS:
        await send_mentor_reaction(context, chat_id, 'long_absence')
        await _send(
            context, chat_id,
            f'{name}, скучали! Тебя не было {_days_ru(days_away)}.\n'
            f'Уровень: {profile["cefr_level"] or "—"}.\n\n'
            'Начнём с плана дня?',
            reply_markup=keyboards.main_menu(),
        )
        return

    if unfinished:
        await send_mentor_reaction(context, chat_id, 'lesson_resume')
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                '▶️ Продолжить урок',
                callback_data=f'lesson:open:{unfinished["lesson_id"]}',
            )],
            [InlineKeyboardButton('📚 План дня', callback_data='plan:menu')],
        ])
        await _send(
            context, chat_id,
            f'{name}, ты не закончила эпизод «{unfinished["title"]}».\n'
            f'Остановились на шаге {unfinished["step_index"] + 1}. Продолжим?',
            reply_markup=kb,
        )
        return

    await send_mentor_reaction(context, chat_id, 'welcome_back')
    await _send(
        context, chat_id,
        f'С возвращением, {name}! 👋\n'
        f'Твой уровень: {profile["cefr_level"] or "—"}.\n\n'
        'Выбери, чем займёмся 👇',
        reply_markup=keyboards.main_menu(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send(
        context, _chat_id(update),
        'Что я умею:\n'
        '📚 Учиться — персональный план на день (чеклист)\n'
        '👤 Профиль — уровень, цель, интересы, напоминания\n'
        '📊 Прогресс — XP, стрик, пройденные уроки\n'
        '🗂 Словарь — слова из уроков с озвучкой\n'
        '📖 Правила — карта грамматики с отметками ✅\n'
        '💬 Наставник — задай вопрос по английскому\n'
        '⭐️ Подписка — полный доступ\n\n'
        'Команды: /start, /diagnostic, /profile, /plan, /tutor\n'
        'В уроках и у наставника можно отвечать текстом или голосом 🎙️\n'
        'Голос распознаётся (нужен Yandex SpeechKit в .env). Кнопка 🔊 озвучивает английский.',
        reply_markup=keyboards.main_menu(),
    )


# --------------------------------------------------------------------------- #
# Diagnostic (adaptive, deterministic checking = 0 tokens)
# --------------------------------------------------------------------------- #

async def diagnostic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_profile(update, context)
    await _begin_diagnostic(update, context)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None
    await show_profile(update, context)


async def lessons_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None
    await show_daily_plan(update, context)


async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = None
    await show_daily_plan(update, context)


async def tutor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_tutor(update, context)


async def _begin_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = await db.get_diagnostic_items()
    chat_id = _chat_id(update)
    if not items:
        await _send(context, chat_id, 'Вопросы для диагностики ещё не добавлены.')
        return

    group: dict[str, list] = {}
    for it in items:
        group.setdefault(it['level'], []).append(it)

    context.user_data['mode'] = 'diagnostic'
    context.user_data['diag'] = {
        'group': group,
        'asked': [],
        'level_idx': 1,  # start at A2
        'count': 0,
        'skill': {},
        'current': None,
    }
    await _send(
        context, chat_id,
        'Начинаем диагностику 🎯\nОтвечай, как можешь — это поможет подобрать уровень.',
    )
    await _ask_next_diagnostic(update, context)


def _pick_diagnostic_item(diag: dict):
    li = diag['level_idx']
    order = [li, li - 1, li + 1, li - 2, li + 2, li - 3, li + 3]
    for idx in order:
        if 0 <= idx <= 3:
            level = db.LEVELS[idx]
            for it in diag['group'].get(level, []):
                if it['id'] not in diag['asked']:
                    return it
    return None


async def _ask_next_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diag = context.user_data['diag']
    chat_id = _chat_id(update)

    if diag['count'] >= MAX_DIAGNOSTIC_QUESTIONS:
        await _finish_diagnostic(update, context)
        return

    item = _pick_diagnostic_item(diag)
    if not item:
        await _finish_diagnostic(update, context)
        return

    diag['current'] = item
    diag['asked'].append(item['id'])
    diag['count'] += 1
    number = diag['count']

    if item['item_type'] == 'listening' and item.get('audio'):
        await _send_media(context, chat_id, item['audio'])

    prompt = f'Вопрос {number}/{MAX_DIAGNOSTIC_QUESTIONS}\n\n{item["prompt"]}'

    # Offer audio when the question itself is in English.
    listen = _is_english(item['prompt'])
    context.user_data['tts_text'] = item['prompt'] if listen else None

    if item['item_type'] in ('multiple_choice', 'listening') and item['options']:
        await _send(context, chat_id, prompt,
                    reply_markup=keyboards.diagnostic_options_kb(item['options'], with_listen=listen))
    elif item['item_type'] == 'speaking':
        hint = '\n\nПроизнеси вслух и пришли голосовое 🎙️ (можно и текстом).'
        await _send(context, chat_id, prompt + hint)
    else:
        await _send(context, chat_id, prompt + '\n\nНапиши ответ сообщением ✍️',
                    reply_markup=keyboards.say_kb() if listen else None)


async def _score_diagnostic_answer(item: dict, answer_text: str, voice_ok: bool = False):
    itype = item['item_type']
    if itype == 'speaking':
        target = ' '.join(item.get('keywords') or []) or item['prompt']
        res = score_speaking(answer_text, target)
        return res.is_correct
    check_type = _DIAG_CHECK_TYPE.get(itype, 'fill_gap')
    result = await checker.check(
        exercise_type=check_type,
        user_answer=answer_text,
        correct=item.get('correct'),
        keywords=item.get('keywords'),
        ai_fallback=False,
    )
    return result.is_correct


async def _handle_diagnostic_answer(update, context, answer_text: str):
    diag = context.user_data.get('diag')
    if not diag or not diag.get('current'):
        return
    item = diag['current']

    is_correct = await _score_diagnostic_answer(item, answer_text)

    skill = item['skill']
    c, t = diag['skill'].get(skill, [0, 0])
    diag['skill'][skill] = [c + (1 if is_correct else 0), t + 1]

    if is_correct:
        diag['level_idx'] = min(3, diag['level_idx'] + 1)
    else:
        diag['level_idx'] = max(0, diag['level_idx'] - 1)

    await _ask_next_diagnostic(update, context)


async def _finish_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diag = context.user_data.get('diag', {})
    chat_id = _chat_id(update)
    level_code = db.LEVELS[diag.get('level_idx', 0)]

    weak = [
        skill for skill, (c, t) in diag.get('skill', {}).items()
        if t > 0 and (c / t) < 0.5
    ]

    profile_id = context.user_data['profile_id']
    await db.finish_diagnostic(profile_id, level_code, weak)

    context.user_data['mode'] = None
    context.user_data['diag'] = None

    weak_text = ''
    if weak:
        names = {
            'grammar': 'грамматика', 'vocabulary': 'лексика',
            'listening': 'аудирование', 'reading': 'чтение',
            'speaking': 'говорение', 'pronunciation': 'произношение',
        }
        weak_text = '\nНад чем поработаем: ' + ', '.join(
            names.get(s, s) for s in weak
        ) + '.'

    await _send(
        context, chat_id,
        f'Готово! Твой уровень: {level_code.upper()} 🎯{weak_text}\n\n'
        'Ещё пара вопросов, чтобы подобрать уроки именно под тебя 👇',
        reply_markup=keyboards.main_menu(),
    )
    # Continue onboarding: goal, then interests.
    context.user_data['onboarding'] = True
    await show_goal(update, context)


# --------------------------------------------------------------------------- #
# Daily plan (adventure chapter — no lesson picker)
# --------------------------------------------------------------------------- #

def _progress_bar(done: int, total: int) -> str:
    if total <= 0:
        return ''
    filled = round(done / total * 6)
    return '●' * filled + '○' * (6 - filled)


def _format_daily_plan_text(plan: dict) -> str:
    episode = plan.get('episode')
    ep_num = (episode or {}).get('episode_num', 0)
    header = f'📖 <b>Глава дня</b>'
    if ep_num:
        header += f' · Эпизод {ep_num}'

    lines = [header, _esc(plan.get('greeting', '')), '']

    if episode:
        lines.append(f'📺 <b>{_esc(episode.get("title", "Эпизод"))}</b>')
        sub = episode.get('subtitle')
        if sub:
            lines.append(_esc(sub))
        mins = episode.get('minutes', 0)
        xp = episode.get('xp_reward', 0)
        meta = []
        if mins:
            meta.append(f'⏱ ~{mins} мин')
        if xp:
            meta.append(f'+{xp} XP')
        if meta:
            lines.append(' · '.join(meta))
        if episode.get('done'):
            lines.append('✅ Глава пройдена')
        lines.append('')
    elif not plan.get('has_episode'):
        lines.append('🎬 Все эпизоды пройдены — скоро новая глава!')
        lines.append('')

    warmup = plan.get('warmup')
    if warmup and not warmup.get('done'):
        from study_app.daily_facts import warmup_label
        _, label = warmup_label(warmup.get('kind', 'fact'))
        lines.append(f'{label} — короткая разминка (1 мин)')
        lines.append('')

    bonus = plan.get('bonus_words')
    if bonus and not bonus.get('done') and (not episode or episode.get('done')):
        lines.append(f'🗂 <b>Бонус:</b> повторить {bonus.get("count", 0)} слов')
        lines.append('')

    done = plan.get('progress_done', 0)
    total = plan.get('progress_total', 1)
    if total > 0:
        bar = _progress_bar(done, total)
        lines.append(f'Прогресс: {bar} {done}/{total}')
        lines.append('')

    if plan.get('all_done'):
        lines.append('🎉 Глава дня закрыта! Завтра — новое приключение.')
    elif episode and not episode.get('done'):
        lines.append('Жми <b>▶️ Продолжить</b> — я поведу по сценарию.')
    elif bonus and not bonus.get('done'):
        lines.append('Остался бонус — закрепи слова за пару минут.')

    if not plan.get('premium'):
        left = plan.get('trial_left', 0)
        lines.append(f'\n<i>Бесплатных эпизодов: {left}</i>')

    return '\n'.join(lines)


async def show_daily_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    chat_id = _chat_id(update)

    if not profile['diagnostic_completed']:
        await _send(context, chat_id,
                    'Сначала пройдём диагностику уровня 🙂',
                    reply_markup=keyboards.start_diagnostic_kb())
        return

    plan = await db.get_daily_plan(profile['id'])
    context.user_data['daily_plan'] = plan

    await _send(
        context, chat_id,
        _format_daily_plan_text(plan),
        reply_markup=keyboards.daily_plan_kb(plan),
        parse_mode=ParseMode.HTML,
    )


async def _show_warmup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
        context.user_data['profile_id'],
    )
    chat_id = _chat_id(update)
    warmup = plan.get('warmup')
    if not warmup:
        await show_daily_plan(update, context)
        return

    context.user_data['tts_text'] = warmup.get('fact_en', '')
    from study_app.daily_facts import warmup_label
    icon, label = warmup_label(warmup.get('kind', 'fact'))
    text = (
        f'{icon} <b>{label}</b>\n\n'
        f'{_esc(warmup.get("fact_ru", ""))}\n\n'
        f'🇬🇧 {_esc(warmup.get("fact_en", ""))}'
    )
    await _send(context, chat_id, text, reply_markup=keyboards.warmup_kb(),
                parse_mode=ParseMode.HTML)


async def _plan_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    plan = await db.get_daily_plan(profile['id'])
    context.user_data['daily_plan'] = plan

    warmup = plan.get('warmup')
    if warmup and not warmup.get('done'):
        await _show_warmup(update, context)
        return

    episode = plan.get('episode')
    if episode and not episode.get('done'):
        await open_lesson(
            update, context, episode['lesson_id'],
            plan_block_id=episode['block_id'],
        )
        return

    bonus = plan.get('bonus_words')
    if bonus and not bonus.get('done'):
        await start_word_review(update, context, from_plan=True)
        return

    await show_daily_plan(update, context)


async def _mark_plan_item_by_type(profile_id: int, plan: dict, item_type: str) -> None:
    for item in plan.get('items', []):
        if item.get('type') == item_type and not item.get('done'):
            await db.mark_plan_block_done(profile_id, item['block_id'])
            item['done'] = True
            break


async def _prompt_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send(
        context, _chat_id(update),
        '🔔 Хочешь, чтобы я напоминал о тренировке каждый день?\n\n'
        'Пришлю интересный факт на двух языках и ссылку на твой план — '
        'можно послушать факт по-английски 🔊',
        reply_markup=keyboards.notification_ask_kb(),
    )


async def show_rules_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    chat_id = _chat_id(update)
    data = await db.get_rules_map(profile['id'])

    if not data.get('topics'):
        await _send(
            context, chat_id,
            'Карта правил пока пуста. Пройди эпизод — правила появятся здесь '
            'после блока грамматики. Или нажми «Выучил» в уроке.',
            reply_markup=keyboards.main_menu(),
        )
        return

    lines = [
        f'📖 <b>Карта правил</b> — твой уровень: {data["level"]}',
        f'Разделов: {len(data["topics"])} · правил: {data.get("total", 0)}',
        '✅ выучил  •  🟢 уже знал  •  ⬜ ещё не отмечено',
        '',
        '<i>Выбери раздел — внутри правила с уровнем и кратким описанием.</i>',
    ]
    context.user_data['rules_topics_map'] = data['topics']
    await _send(
        context, chat_id, '\n'.join(lines),
        reply_markup=keyboards.rules_topics_kb(data['topics']),
        parse_mode=ParseMode.HTML,
    )


async def show_rules_topic(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    topic: str,
    rules: list[dict],
):
    chat_id = _chat_id(update)
    lines = [f'📂 <b>{_esc(topic)}</b>', '']
    for rule in rules:
        level = rule.get('level', '')
        summary = rule.get('summary_ru', '')
        line = f'{rule["mark"]} <b>[{level}]</b> {_esc(rule["title"])}'
        if summary:
            line += f'\n   <i>{_esc(summary)}</i>'
        lines.append(line)
        lines.append('')
    lines.append('<i>Нажми правило — откроется таблица и примеры.</i>')
    await _send(
        context, chat_id, '\n'.join(lines),
        reply_markup=keyboards.rules_topic_kb(topic, rules),
        parse_mode=ParseMode.HTML,
    )


def _rule_to_html(rule: dict) -> str:
    step = {
        'title': rule.get('title'),
        'content': {
            'rule_ru': rule.get('summary_ru', ''),
            'table': rule.get('table', {}),
            'examples': rule.get('examples', []),
            'tip_ru': rule.get('tip_ru', ''),
        },
    }
    return _grammar_html(step)


async def show_rule_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, rule_key: str):
    rule = await db.get_rule_detail(context.user_data['profile_id'], rule_key)
    chat_id = _chat_id(update)
    if not rule:
        await _send(context, chat_id, 'Правило не найдено.', reply_markup=keyboards.main_menu())
        return
    status_note = ''
    if rule.get('status') == 'learned':
        status_note = '\n\n✅ В твоей библиотеке'
    elif rule.get('status') == 'known':
        status_note = '\n\n🟢 Отмечено как «уже знаю»'
    context.user_data['tts_text'] = _grammar_speak_text({
        'table': rule.get('table', {}),
        'examples': rule.get('examples', []),
    }) or ''
    await _send(
        context, chat_id, _rule_to_html(rule) + status_note,
        reply_markup=keyboards.rule_detail_kb(rule_key, rule.get('status', '')),
        parse_mode=ParseMode.HTML,
    )


async def _show_exercise_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('current_step') or {}
    content = step.get('content') or {}
    chat_id = _chat_id(update)

    if content.get('hint_detail_ru'):
        text = content['hint_detail_ru']
        if not text.startswith('<') and not text.startswith('📖'):
            text = f'💡 {_esc(text)}'
    elif content.get('rule_key'):
        rule = await db.get_rule_detail(
            context.user_data['profile_id'], content['rule_key'],
        )
        if rule:
            text = _grammar_html({
                'title': rule.get('title'),
                'content': {
                    'rule_ru': rule.get('summary_ru', ''),
                    'table': rule.get('table', {}),
                    'examples': rule.get('examples', []),
                    'tip_ru': rule.get('tip_ru', ''),
                },
            })
        else:
            text = '💡 Правило скоро появится в библиотеке.'
    elif content.get('hint_ru'):
        text = f'💡 {_esc(content["hint_ru"])}'
    else:
        text = 'Подсказка к этому заданию пока не добавлена.'

    await _send(context, chat_id, text, parse_mode=ParseMode.HTML)


async def start_rule_drill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile_id = context.user_data['profile_id']
    chat_id = _chat_id(update)
    drill = await db.get_rule_drill(profile_id)
    if not drill:
        await _send(
            context, chat_id,
            'Все правила отмечены — отлично! 🎉 Новые появятся в следующих эпизодах.',
            reply_markup=keyboards.main_menu(),
        )
        return
    context.user_data['mode'] = 'rule_drill'
    context.user_data['rule_drill'] = drill
    prompt = drill['prompt_ru']
    if drill.get('hint_ru'):
        prompt += f'\n\n💡 {drill["hint_ru"]}'
    await _send(
        context, chat_id, f'🐦 Тренировка правил\n\n{prompt}',
        reply_markup=keyboards.exercise_options_kb(
            drill['options'], with_hint=False, with_ask=True,
        ),
    )


# --------------------------------------------------------------------------- #
# Lessons: menu + engine
# --------------------------------------------------------------------------- #

async def show_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy lesson list — redirects to the daily plan."""
    await show_daily_plan(update, context)


async def open_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE, lesson_id: int,
                      *, plan_block_id: int | None = None):
    profile_id = context.user_data['profile_id']
    chat_id = _chat_id(update)

    gate = await db.can_start_lesson(profile_id, lesson_id)
    if not gate['allowed']:
        await _show_paywall(update, context)
        return

    flow = await db.get_lesson_flow(lesson_id)
    if not flow or not flow['steps']:
        await _send(context, chat_id, 'Этот урок ещё не наполнен.',
                    reply_markup=keyboards.main_menu())
        return

    progress = await db.start_or_resume_lesson(profile_id, lesson_id)

    context.user_data['mode'] = 'lesson'
    context.user_data['plan_episode_block_id'] = plan_block_id
    step_idx = progress.get('current_step_index', 0)
    context.user_data['lesson'] = {
        'lesson_id': lesson_id,
        'steps': flow['steps'],
        'index': step_idx,
        'character': flow.get('character'),
        'level': flow['level'],
        'title': flow['title'],
    }
    context.user_data['spirit_after_wrong'] = False
    context.user_data['spirit_since_success'] = 0

    if step_idx == 0:
        await send_mentor_reaction(context, chat_id, 'lesson_start')
        intro = flow.get('intro_text') or f'▶️ Эпизод: {flow["title"]}'
        await _send(context, chat_id, intro)
    else:
        await send_mentor_reaction(context, chat_id, 'lesson_resume')
        await _send(
            context, chat_id,
            f'Продолжаем «{flow["title"]}» — шаг {step_idx + 1} из {len(flow["steps"])}.',
        )
    await _render_step(update, context)


async def _advance(update, context):
    state = context.user_data.get('lesson')
    if not state:
        return
    state['index'] += 1
    await db.save_step_index(
        context.user_data['profile_id'], state['lesson_id'], state['index'],
    )
    await _render_step(update, context)


def _compose_step_text(step: dict) -> str:
    parts = []
    if step.get('title'):
        parts.append(step['title'])
    if step.get('text'):
        parts.append(step['text'])

    content = step.get('content') or {}
    if step['step_type'] == 'vocabulary' and content.get('words'):
        lines = ['📖 Слова:']
        for w in content['words']:
            line = f'• {w.get("en", "")} — {w.get("ru", "")}'
            if w.get('example'):
                if w.get('example_ru'):
                    line += f'\n   ({w["example_ru"]})'
                line += f'\n   🇬🇧 {w["example"]}'
            lines.append(line)
        parts.append('\n'.join(lines))

    if step['step_type'] == 'dialogue' and content.get('lines'):
        lines = []
        for ln in content['lines']:
            speaker = ln.get('speaker', '')
            en = ln.get('text', '')
            ru = ln.get('ru', '')
            row = f'{speaker}: 🇬🇧 {en}' if speaker else f'🇬🇧 {en}'
            if ru:
                row += f'\n   ({ru})'
            lines.append(row)
        parts.append('\n'.join(lines))

    return '\n\n'.join(p for p in parts if p) or '…'


async def _render_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('lesson')
    chat_id = _chat_id(update)
    if not state:
        return

    steps = state['steps']
    idx = state['index']
    if idx >= len(steps):
        await _finish_lesson(update, context)
        return

    step = steps[idx]
    stype = step['step_type']
    content = step.get('content') or {}
    context.user_data['current_step'] = step

    scene_key = content.get('scene_key')
    if stype == 'cliffhanger':
        await send_mentor_reaction(context, chat_id, 'cliffhanger')
    if scene_key and stype in ('hook', 'story', 'cliffhanger'):
        await send_media_by_key(context, chat_id, scene_key)

    # Media-first for visual/audio steps.
    if step.get('media'):
        await _send_media(context, chat_id, step['media'])

    # ---- Interactive steps -------------------------------------------- #
    if stype == 'exercise':
        personalized = False
        if content.get('personalize'):
            await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
            topic = context.user_data.get('sphere_en') or ''
            gen = await generate_practice(
                level=state.get('level', 'a2'),
                skill=content.get('skill') or step.get('skill') or 'grammar',
                topic=topic,
                user_key=context.user_data.get('user_key'),
            )
            content = {
                **content,
                'exercise_type': gen.get('exercise_type', 'multiple_choice'),
                'options': gen.get('options', []),
                'correct': gen.get('correct', []),
                'explanation': gen.get('explanation', ''),
            }
            step = {**step, 'content': content, 'text': gen.get('prompt') or step.get('text')}
            context.user_data['current_step'] = step
            personalized = True

        etype = content.get('exercise_type', 'short_answer')
        prompt = step.get('text') or content.get('prompt', 'Задание:')
        if personalized:
            prompt = '🎧 Персонально для тебя:\n\n' + prompt

        if etype == 'matching' and content.get('pairs'):
            pairs = content['pairs']
            pool = list({p['right'] for p in pairs})
            for d in content.get('distractors') or []:
                if d not in pool:
                    pool.append(d)
            context.user_data['matching'] = {
                'pairs': pairs,
                'pool': pool,
                'index': 0,
                'correct_count': 0,
                'step_id': step['id'],
                'intro': prompt,
            }
            context.user_data['expect'] = 'ex_match'
            await _show_matching_pair(update, context)
            return

        if etype in ('multiple_choice', 'true_false') and content.get('options'):
            context.user_data['expect'] = 'ex_choice'
            english_opts = [o for o in content['options'] if _is_english(o)]
            context.user_data['tts_text'] = '. '.join(english_opts) or None
            has_hint = _exercise_has_hint(content)
            await _send(
                context, chat_id, prompt,
                reply_markup=keyboards.exercise_options_kb(
                    content['options'],
                    with_listen=bool(english_opts),
                    with_ask=True,
                    with_hint=has_hint,
                ),
                parse_mode=ParseMode.HTML if _step_uses_html(step) else None,
            )
        else:
            voice_ok = _exercise_accepts_voice(content, etype)
            context.user_data['expect'] = 'ex_text_or_voice' if voice_ok else 'ex_text'
            hint = '\n\nНапиши ответ ✍️'
            if voice_ok:
                hint += ' или пришли голосовое 🎙️ (на английском)'
            has_hint = _exercise_has_hint(content)
            if has_hint:
                hint += '\n<i>Застрял? Нажми 💡 Подсказка</i>'
            kb = keyboards.exercise_text_kb(with_hint=has_hint, with_ask=True)
            await _send(
                context, chat_id, prompt + hint,
                reply_markup=kb,
                parse_mode=ParseMode.HTML if _step_uses_html(step) else None,
            )
        return

    if stype == 'speaking':
        context.user_data['expect'] = 'ex_voice'
        target = content.get('target', '')
        await _send(
            context, chat_id,
            (step.get('text') or 'Произнеси вслух:') +
            (f'\n\n🗣️ «{target}»' if target else '') +
            '\n\nПришли голосовое 🎙️ (или напиши текстом).',
            reply_markup=keyboards.listen_kb() if target else None,
        )
        return

    if stype == 'ai_dialogue':
        await _start_ai_dialogue(update, context, step)
        return

    # ---- Grammar rule: bilingual, table-first (HTML) ------------------- #
    if stype == 'grammar_note':
        await send_mentor_reaction(context, chat_id, 'grammar_note')
        speak_text = _speak_text_for_step(step)
        if speak_text:
            context.user_data['tts_text'] = speak_text
        content = step.get('content') or {}
        rule_key = content.get('rule_key', '')
        if rule_key:
            kb = keyboards.grammar_rule_kb(rule_key)
        elif speak_text:
            kb = keyboards.lesson_help_kb()
        else:
            kb = keyboards.continue_kb()
        await _send(context, chat_id, _grammar_html(step),
                    reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    # ---- Content steps ------------------------------------------------- #
    speak_text = _speak_text_for_step(step)
    if speak_text:
        context.user_data['tts_text'] = speak_text

    # An "audio" step with no uploaded media is voiced on the fly via TTS.
    if stype == 'audio' and not step.get('media') and speak_text:
        await _send_tts(context, chat_id, speak_text)

    text = _compose_step_text(step)
    label = '🎉 Забрать награду' if stype == 'reward' else '➡️ Далее'
    if speak_text and stype not in ('reward', 'cliffhanger'):
        kb = keyboards.lesson_help_kb(label)
    elif speak_text:
        kb = keyboards.continue_with_listen_kb(label)
    else:
        kb = keyboards.continue_kb(label)
    parse_mode = ParseMode.HTML if _step_uses_html(step) else None
    await _send(context, chat_id, text, reply_markup=kb, parse_mode=parse_mode)


async def _handle_exercise_text(update, context, answer_text: str, is_voice=False):
    step = context.user_data.get('current_step')
    chat_id = _chat_id(update)
    if not step:
        return
    content = step.get('content') or {}
    etype = content.get('exercise_type', 'short_answer')
    user_key = context.user_data.get('user_key')

    if context.user_data.get('expect') == 'ex_voice':
        target = content.get('target', '')
        result = score_speaking(answer_text, target)
        result_dict = _result_to_dict(result)
    else:
        result = await checker.check(
            exercise_type=etype,
            user_answer=answer_text,
            correct=content.get('correct'),
            keywords=content.get('keywords'),
            task_prompt=step.get('text') or content.get('prompt', ''),
            level=context.user_data.get('lesson', {}).get('level', 'a2'),
            ai_fallback=bool(content.get('ai_fallback')),
            ai_check_prompt=content.get('ai_check_prompt', ''),
            user_key=user_key,
        )
        result_dict = _result_to_dict(result)

    await _deliver_feedback(context, chat_id, result, content, is_voice=is_voice)
    await db.record_attempt(
        context.user_data['profile_id'],
        context.user_data['lesson']['lesson_id'],
        step['id'], answer_text, result_dict,
    )
    context.user_data['expect'] = None
    await _advance(update, context)


async def _handle_rule_drill_choice(update, context, option_index: int):
    drill = context.user_data.get('rule_drill') or {}
    chat_id = _chat_id(update)
    options = drill.get('options', [])
    if option_index >= len(options):
        return
    chosen = options[option_index]
    correct = drill.get('correct', [])
    is_ok = chosen in correct
    if is_ok:
        await db.set_user_rule_status(
            context.user_data['profile_id'], drill['rule_key'], 'learned',
        )
        msg = '✅ Верно! Правило добавлено в библиотеку.'
    else:
        msg = f'❌ Правильный вариант: {correct[0] if correct else "—"}'
    context.user_data['mode'] = None
    context.user_data['rule_drill'] = None
    plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
        context.user_data['profile_id'],
    )
    await _mark_plan_item_by_type(context.user_data['profile_id'], plan, 'rules')
    await _send(context, chat_id, msg)
    await show_daily_plan(update, context)


def _matching_options(pool: list[str], correct: str) -> list[str]:
    opts = [correct]
    for item in pool:
        if item != correct and item not in opts:
            opts.append(item)
        if len(opts) >= 4:
            break
    random.shuffle(opts)
    return opts


async def _show_matching_pair(update, context):
    """One pair at a time: pick the Russian translation."""
    m = context.user_data.get('matching')
    chat_id = _chat_id(update)
    if not m:
        return
    idx = m['index']
    pairs = m['pairs']
    if idx >= len(pairs):
        return
    pair = pairs[idx]
    options = _matching_options(m['pool'], pair['right'])
    m['options'] = options
    context.user_data['tts_text'] = pair['left']
    intro = m.get('intro') or 'Выбери правильный перевод:'
    step = context.user_data.get('current_step') or {}
    content = step.get('content') or {}
    has_hint = _exercise_has_hint(content)
    prompt = (
        f'✏️ <b>{_esc(intro)}</b>\n\n'
        f'({idx + 1}/{len(pairs)})\n\n'
        f'🇬🇧 <b>{_esc(pair["left"])}</b>'
    )
    await _send(
        context, chat_id, prompt,
        reply_markup=keyboards.exercise_options_kb(
            options, with_listen=True, with_ask=True, with_hint=has_hint,
        ),
        parse_mode=ParseMode.HTML,
    )


async def _handle_matching_choice(update, context, option_index: int):
    m = context.user_data.get('matching')
    chat_id = _chat_id(update)
    step = context.user_data.get('current_step')
    if not m or not step:
        return
    options = m.get('options') or []
    if option_index >= len(options):
        return
    pair = m['pairs'][m['index']]
    chosen = options[option_index]
    ok = chosen == pair['right']
    if ok:
        m['correct_count'] += 1
        await _send(context, chat_id, f'✅ Верно: {_esc(pair["left"])} — {_esc(pair["right"])}')
    else:
        await _send(
            context, chat_id,
            f'❌ Не совсем. {_esc(pair["left"])} — <b>{_esc(pair["right"])}</b>',
            parse_mode=ParseMode.HTML,
        )
    m['index'] += 1
    if m['index'] < len(m['pairs']):
        await _show_matching_pair(update, context)
        return

    total = len(m['pairs'])
    hits = m['correct_count']
    content = step.get('content') or {}
    summary_ok = hits == total
    icon = '🎯' if summary_ok else '💪'
    await _send(
        context, chat_id,
        f'{icon} Готово: {hits}/{total} верных ответов.'
        + (f'\n{content.get("explanation", "")}' if content.get('explanation') else ''),
    )
    await db.record_attempt(
        context.user_data['profile_id'],
        context.user_data['lesson']['lesson_id'],
        step['id'],
        f'{hits}/{total}',
        {
            'is_correct': summary_ok,
            'score': hits / total if total else 0,
            'feedback_ru': f'{hits}/{total}',
            'used_ai': False,
            'method': 'matching',
        },
    )
    context.user_data['matching'] = None
    context.user_data['expect'] = None
    await _advance(update, context)


async def _handle_exercise_choice(update, context, option_index: int):
    if context.user_data.get('expect') == 'ex_match':
        await _handle_matching_choice(update, context, option_index)
        return
    step = context.user_data.get('current_step')
    chat_id = _chat_id(update)
    if not step:
        return
    content = step.get('content') or {}
    options = content.get('options', [])
    if option_index >= len(options):
        return
    chosen = options[option_index]

    result = await checker.check(
        exercise_type=content.get('exercise_type', 'multiple_choice'),
        user_answer=chosen,
        correct=content.get('correct'),
    )
    await _deliver_feedback(context, chat_id, result, content)
    await db.record_attempt(
        context.user_data['profile_id'],
        context.user_data['lesson']['lesson_id'],
        step['id'], chosen, _result_to_dict(result),
    )
    context.user_data['expect'] = None
    await _advance(update, context)


def _result_to_dict(result) -> dict:
    return {
        'is_correct': result.is_correct,
        'score': result.score,
        'feedback_ru': result.feedback_ru,
        'used_ai': result.used_ai,
        'method': result.method,
    }


async def _deliver_feedback(context, chat_id, result, content: dict, *, is_voice: bool = False):
    if result.is_correct:
        if should_show_correct_spirit(context.user_data):
            await send_mentor_reaction(context, chat_id, 'answer_correct')
            mark_correct_spirit_shown(context.user_data)
        else:
            tick_spirit_exercise(context.user_data)
    else:
        await send_mentor_reaction(context, chat_id, 'answer_wrong')
        mark_wrong_spirit_shown(context.user_data)

    icon = '✅' if result.is_correct else '❌'
    msg = f'{icon} {result.feedback_ru}'.strip()
    if result.correction and not result.is_correct:
        msg += f'\n✍️ Правильно: {result.correction}'
    if result.tip_ru:
        msg += f'\n💡 {result.tip_ru}'
    if not result.is_correct and content.get('explanation'):
        msg += f'\nℹ️ {content["explanation"]}'
    if is_voice and result.is_correct:
        msg += '\n🎙️ Отличная практика говорения!'

    # Let the learner hear the correct English version.
    speak = result.correction if _is_english(result.correction) else None
    if not speak:
        correct = content.get('correct') or []
        if correct and _is_english(str(correct[0])):
            speak = str(correct[0])
    context.user_data['tts_text'] = speak
    await _send(context, chat_id, msg,
                reply_markup=keyboards.say_kb() if speak else None)


# --------------------------------------------------------------------------- #
# AI dialogue step
# --------------------------------------------------------------------------- #

async def _start_ai_dialogue(update, context, step):
    content = step.get('content') or {}
    chat_id = _chat_id(update)
    character = step.get('character') or context.user_data.get('lesson', {}).get('character') or {}
    opening = content.get('opening') or "Hi! Let's chat a little."

    context.user_data['mode'] = 'dialogue'
    context.user_data['dialogue'] = {
        'history': [ChatMessage('assistant', opening)],
        'turns_left': int(content.get('turns', settings.AI_HISTORY_MESSAGES // 2 or 4)),
        'situation': content.get('situation', 'friendly small talk'),
        'character': character,
        'level': context.user_data.get('lesson', {}).get('level', 'a2'),
    }
    await _send_character_turn(
        context, chat_id,
        character=character,
        text=opening,
        reply_markup=keyboards.finish_dialogue_kb(),
    )


async def _handle_dialogue_turn(update, context, user_text: str):
    dlg = context.user_data.get('dialogue')
    chat_id = _chat_id(update)
    if not dlg:
        return

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    dlg['history'].append(ChatMessage('user', user_text))
    character = dlg.get('character') or {}

    reply = await partner.reply(
        history=dlg['history'],
        character_name=character.get('name', 'Emma'),
        character_role=character.get('role', 'friendly guide'),
        personality=character.get('personality', ''),
        speaking_style=character.get('speaking_style', ''),
        level=dlg.get('level', 'a2'),
        situation=dlg.get('situation', 'small talk'),
        user_key=context.user_data.get('user_key'),
    )
    dlg['history'].append(ChatMessage('assistant', reply))
    dlg['turns_left'] -= 1

    if dlg['turns_left'] <= 0:
        await _send_character_turn(
            context, chat_id,
            character=character,
            text=reply,
            reply_markup=keyboards.say_kb(),
            show_video=False,
        )
        await _finish_dialogue(update, context)
    else:
        await _send_character_turn(
            context, chat_id,
            character=character,
            text=reply,
            reply_markup=keyboards.finish_dialogue_kb(),
            show_video=False,
        )


async def _finish_dialogue(update, context):
    context.user_data['dialogue'] = None
    context.user_data['mode'] = 'lesson'
    unlocked = await db.unlock_achievement(
        context.user_data['profile_id'], 'first-ai-dialogue',
    )
    if unlocked:
        await _send(context, _chat_id(update),
                    f'{unlocked.get("icon", "🏆")} Достижение: {unlocked["title"]}!')
    await _advance(update, context)


# --------------------------------------------------------------------------- #
# Finish lesson + gamification
# --------------------------------------------------------------------------- #

async def _finish_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('lesson') or {}
    chat_id = _chat_id(update)
    lesson_id = state.get('lesson_id')

    # Harvest vocabulary into the learner's personal dictionary (SRS) before reset.
    vocab_words = []
    for step in state.get('steps', []):
        if step.get('step_type') == 'vocabulary':
            vocab_words.extend((step.get('content') or {}).get('words', []))
    if vocab_words:
        await db.save_lesson_words(context.user_data['profile_id'], vocab_words)

    summary = await db.complete_lesson(context.user_data['profile_id'], lesson_id)
    plan_block_id = context.user_data.pop('plan_episode_block_id', None)
    if plan_block_id:
        await db.mark_plan_block_done(context.user_data['profile_id'], plan_block_id)
    context.user_data['mode'] = None
    context.user_data['lesson'] = None
    context.user_data['expect'] = None

    lines = [
        '🎉 Урок пройден!',
        f'Правильных ответов: {summary["correct"]}/{summary["total"]}'
        if summary['total'] else 'Отличная работа!',
        f'+{summary["xp_earned"]} XP  •  всего {summary["total_xp"]} XP',
        f'🔥 Стрик: {summary["streak"]} дн.  •  Игровой уровень {summary["level"]}',
    ]
    if summary.get('level_up'):
        lines.append(f'⬆️ Новый игровой уровень {summary["level"]}! Так держать 💪')
    for ach in summary.get('unlocked', []):
        lines.append(f'{ach.get("icon", "🏆")} Достижение: {ach["title"]}!')
    if summary.get('level_up'):
        await send_mentor_reaction(context, chat_id, 'lesson_complete_big')
    else:
        await send_mentor_reaction(context, chat_id, 'lesson_complete')
    await _send(context, chat_id, '\n'.join(lines))

    if summary.get('need_paywall'):
        await _show_paywall(update, context)
        return

    profile = await db.get_profile(context.user_data['profile_id'])
    if profile.get('weak_skills'):
        weak_ru = ', '.join(db.SKILL_RU.get(s, s) for s in profile['weak_skills'])
        await _send(
            context, chat_id,
            f'Хочешь закрепить слабые темы ({weak_ru})? '
            'Я подберу короткое персональное задание 👇',
            reply_markup=keyboards.practice_offer_kb(),
        )
    else:
        await _send(context, chat_id, 'Возвращаемся к плану дня 👇')
        await show_daily_plan(update, context)


# --------------------------------------------------------------------------- #
# Personalized practice (AI-generated, targets weak skills)
# --------------------------------------------------------------------------- #

async def start_weak_practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    chat_id = _chat_id(update)

    weak = profile.get('weak_skills') or []
    skill = weak[0] if weak else 'grammar'

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    exercise = await generate_practice(
        level=profile.get('level_code', 'a2'),
        skill=skill,
        user_key=context.user_data.get('user_key'),
    )

    context.user_data['mode'] = 'practice'
    context.user_data['practice'] = exercise

    prompt = f'🎯 Практика ({db.SKILL_RU.get(skill, skill)}):\n\n{exercise["prompt"]}'
    if exercise.get('exercise_type') == 'multiple_choice' and exercise.get('options'):
        context.user_data['practice_expect'] = 'choice'
        await _send(context, chat_id, prompt,
                    reply_markup=keyboards.practice_options_kb(exercise['options']))
    else:
        context.user_data['practice_expect'] = 'text'
        await _send(context, chat_id, prompt + '\n\nНапиши ответ ✍️ или пришли голосовое 🎙️')


async def _deliver_practice_feedback(update, context, user_answer: str):
    exercise = context.user_data.get('practice') or {}
    chat_id = _chat_id(update)

    result = await checker.check(
        exercise_type=exercise.get('exercise_type', 'multiple_choice'),
        user_answer=user_answer,
        correct=exercise.get('correct'),
    )
    icon = '✅' if result.is_correct else '❌'
    msg = f'{icon} {result.feedback_ru}'.strip()
    correct = exercise.get('correct') or []
    if not result.is_correct and correct:
        msg += f'\n✍️ Правильно: {correct[0]}'
    if exercise.get('explanation'):
        msg += f'\nℹ️ {exercise["explanation"]}'

    context.user_data['mode'] = None
    context.user_data['practice_expect'] = None
    await _send(context, chat_id, msg, reply_markup=keyboards.practice_again_kb())


async def _handle_practice_choice(update, context, option_index: int):
    exercise = context.user_data.get('practice') or {}
    options = exercise.get('options', [])
    if option_index >= len(options):
        return
    await _deliver_practice_feedback(update, context, options[option_index])


# --------------------------------------------------------------------------- #
# Progress / dictionary
# --------------------------------------------------------------------------- #

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    data = await db.get_progress_summary(profile['id'])
    sub = (f'Активна до {data["subscription_until"]}'
           if data['subscription_until'] else 'нет активной подписки')
    await _send(
        context, _chat_id(update),
        '📊 Твой прогресс\n\n'
        f'Уровень английского: {data["level"]}\n'
        f'XP: {data["xp"]}  •  Игровой уровень: {data["user_level"]}\n'
        f'🔥 Стрик: {data["streak"]} дн. (рекорд {data["longest_streak"]})\n'
        f'Пройдено уроков: {data["completed_lessons"]}\n'
        f'Пробные уроки: {data["trial_used"]}/{data["trial_limit"]}\n'
        f'Подписка: {sub}',
        reply_markup=keyboards.main_menu(),
    )


_WORD_STATUS_ICON = {
    'new': '🆕', 'learning': '📗', 'known': '✅', 'mastered': '🌟',
}


async def show_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    words = await db.get_dictionary_words(profile['id'])
    if not words:
        await _send(context, _chat_id(update),
                    'Словарь пока пуст 📖\n\nСлова добавляются автоматически из '
                    'пройденных уроков. Пройди урок — и они появятся здесь для '
                    'тренировки с озвучкой.',
                    reply_markup=keyboards.main_menu())
        return
    lines = ['🗂 Твой словарь:\n']
    speak_chunks = []
    for w in words:
        icon = _WORD_STATUS_ICON.get(w.get('status'), '•')
        line = f'{icon} {w["english"]} — {w["translation"]}'
        if w.get('example'):
            line += f'\n   {w["example"]}'
        lines.append(line)
        speak_chunks.append(
            w['english'] if not w.get('example') else f'{w["english"]}. {w["example"]}'
        )
    context.user_data['dict_speak'] = '. '.join(speak_chunks)
    await _send(context, _chat_id(update), '\n'.join(lines),
                reply_markup=keyboards.dict_listen_kb(has_words=True))


# --------------------------------------------------------------------------- #
# Vocabulary spaced-repetition review
# --------------------------------------------------------------------------- #

async def start_word_review(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            *, from_plan: bool = False):
    profile = await _ensure_profile(update, context)
    chat_id = _chat_id(update)

    if context.user_data.get('mode') == 'review' and context.user_data.get('review_queue'):
        return

    due = await db.get_due_words(profile['id'], limit=8)
    if not due:
        if from_plan:
            plan = context.user_data.get('daily_plan') or await db.get_daily_plan(profile['id'])
            await _mark_plan_item_by_type(profile['id'], plan, 'words')
        await _send(context, chat_id,
                    'Сейчас нет слов к повторению 👍 Загляни позже или пройди '
                    'новый эпизод, чтобы добавить слова.',
                    reply_markup=keyboards.main_menu())
        if from_plan:
            await show_daily_plan(update, context)
        return
    context.user_data['mode'] = 'review'
    context.user_data['review_from_plan'] = from_plan
    context.user_data['review_queue'] = due
    await send_mentor_reaction(context, chat_id, 'word_review')
    await _send(
        context, chat_id,
        f'🎓 Тренировка слов ({len(due)} шт.)\n'
        'Показываю перевод — <b>напиши или скажи</b> одно слово по-английски.\n'
        '✍️ текстом  ·  🎙️ голосом',
        parse_mode=ParseMode.HTML,
    )
    await _ask_next_word(update, context)


async def _ask_next_word(update, context):
    queue = context.user_data.get('review_queue') or []
    chat_id = _chat_id(update)
    if not queue:
        context.user_data['mode'] = None
        from_plan = context.user_data.pop('review_from_plan', False)
        await _send(context, chat_id, '🎉 Повторение завершено! Отличная работа.')
        if from_plan:
            plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
                context.user_data['profile_id'],
            )
            await _mark_plan_item_by_type(context.user_data['profile_id'], plan, 'words')
            await show_daily_plan(update, context)
        else:
            await _send(context, chat_id, '👇', reply_markup=keyboards.main_menu())
        return
    word = queue.pop(0)
    context.user_data['review_current'] = word
    await _send(
        context, chat_id,
        f'Как по-английски: «{word["translation"]}»?\n'
        '✍️ Напиши  ·  🎙️ Скажи',
        parse_mode=ParseMode.HTML,
    )


async def _handle_word_review_answer(update, context, answer_text: str):
    word = context.user_data.get('review_current')
    chat_id = _chat_id(update)
    if not word:
        return

    correct, guess, ratio = score_word_review(answer_text, word['english'])

    await db.record_word_review(context.user_data['profile_id'], word['word_id'], correct)

    if correct:
        msg = f'✅ Верно: {word["english"]}'
        if guess and normalize(guess) != normalize(word['english']) and answer_text.strip():
            msg += f'\n(услышал: «{guess}»)'
    else:
        msg = f'❌ Правильно: {word["english"]} — {word["translation"]}'
        if answer_text.strip():
            msg += f'\n(услышал: «{answer_text.strip()}»)'
    if word.get('example'):
        msg += f'\n📝 {word["example"]}'

    # Voice the English word (+ example) so the learner hears it.
    context.user_data['tts_text'] = (
        word['english'] if not word.get('example')
        else f'{word["english"]}. {word["example"]}'
    )
    await _send(context, chat_id, msg, reply_markup=keyboards.srs_next_kb())


# --------------------------------------------------------------------------- #
# Profile & onboarding pickers
# --------------------------------------------------------------------------- #

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    chat_id = _chat_id(update)

    if not profile['diagnostic_completed']:
        await _send(context, chat_id,
                    'Сначала пройдём диагностику уровня 🙂',
                    reply_markup=keyboards.start_diagnostic_kb())
        return

    d = await db.get_profile_detail(profile['id'])
    name = d['first_name'] or 'друг'

    unlocked = [a for a in d['achievements'] if a['unlocked']]
    ach_line = (
        ' '.join(a['icon'] for a in unlocked) if unlocked else 'пока нет — всё впереди!'
    )
    sub = (f'активна до {d["subscription_until"]}'
           if d['subscription_until'] else 'нет активной')
    interests = ', '.join(d['interests']) if d['interests'] else 'не выбраны'
    weak = ', '.join(d['weak_skills_ru']) if d['weak_skills_ru'] else '—'

    text = (
        f'👤 Профиль — {name}\n\n'
        f'🎯 Уровень английского: {d["level"]}\n'
        f'🎓 Цель: {d["goal"] or "не выбрана"}\n'
        f'💼 Сфера: {d.get("sphere") or "не выбрана"}\n'
        f'❤️ Интересы: {interests}\n'
        f'📉 Над чем работаем: {weak}\n\n'
        f'⭐️ XP: {d["xp"]} (до уровня {d["user_level"] + 1} осталось {d["xp_to_next"]})\n'
        f'🎮 Игровой уровень: {d["user_level"]}\n'
        f'🔥 Стрик: {d["streak"]} дн. (рекорд {d["longest_streak"]})\n'
        f'📚 Пройдено уроков: {d["completed_lessons"]}\n'
        f'🎟 Пробные уроки: {d["trial_used"]}/{d["trial_limit"]}\n'
        f'💳 Подписка: {sub}\n\n'
        f'🏆 Достижения: {ach_line}'
    )
    await _send(context, chat_id, text, reply_markup=keyboards.profile_kb())


async def show_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    items = await db.get_interests()
    if not items:
        await _send(context, _chat_id(update),
                    'Список интересов ещё не настроен.', reply_markup=keyboards.main_menu())
        return
    selected = set(await db.get_user_interest_ids(profile['id']))
    await _send(
        context, _chat_id(update),
        'Выбери, что тебе интересно — я буду подбирать уроки под это 👇\n'
        '(нажимай, чтобы отметить; потом «Готово»)',
        reply_markup=keyboards.interests_kb(items, selected),
    )


async def _refresh_interests(update, context):
    profile_id = context.user_data['profile_id']
    items = await db.get_interests()
    selected = set(await db.get_user_interest_ids(profile_id))
    try:
        await update.callback_query.edit_message_reply_markup(
            reply_markup=keyboards.interests_kb(items, selected)
        )
    except Exception:  # noqa: BLE001
        pass


async def show_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    d = await db.get_profile_detail(profile['id'])
    goals = db.learning_goal_choices()
    current = ''
    for g in goals:
        if g['label'] == d['goal']:
            current = g['code']
    await _send(
        context, _chat_id(update),
        'Зачем тебе английский? Это поможет подобрать темы уроков 👇',
        reply_markup=keyboards.goal_kb(goals, current),
    )


async def show_sphere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    current = profile.get('profession', '')
    await _send(
        context, _chat_id(update),
        'В какой сфере ты работаешь или учишься? '
        'Буду иногда давать практику из твоей области 👇\n'
        '(можно пропустить — нажми «🏠 В меню»)',
        reply_markup=keyboards.sphere_kb(db.sphere_choices(), current),
    )


# --------------------------------------------------------------------------- #
# Ask the tutor (free-form AI help)
# --------------------------------------------------------------------------- #

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    context.user_data['mode'] = 'tutor'
    context.user_data['tutor_history'] = [
        ChatMessage(
            'assistant',
            "Hi! I'm your English tutor. Ask me anything about English — "
            'grammar, words, or how to say something.',
        )
    ]
    context.user_data['tutor_level'] = profile.get('level_code', 'a2')
    await _send(
        context, _chat_id(update),
        '💬 Режим наставника включён.\n\n'
        'Задай вопрос по английскому (можно по-русски): грамматика, перевод, '
        '«как сказать…», разбор ошибки. Можно написать или записать голосом 🎙️ — '
        'я распознаю речь и отвечу.\n'
        'Попробуй и потренируй произношение: задай вопрос на английском вслух.\n\n'
        'Чтобы выйти — нажми любую кнопку меню 👇',
        reply_markup=keyboards.main_menu(),
    )


async def _handle_tutor_turn(update, context, user_text: str):
    chat_id = _chat_id(update)
    history = context.user_data.get('tutor_history') or []

    # Deterministic-first: answer common grammar questions for free (0 tokens).
    canned = explain_grammar(user_text)
    if canned:
        history.append(ChatMessage('user', user_text))
        history.append(ChatMessage('assistant', canned))
        context.user_data['tutor_history'] = history[-12:]
        kb = None
        if context.user_data.get('lesson_help_return'):
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton('↩️ Вернуться к уроку', callback_data='lesson:resume'),
            ]])
        await _send(context, chat_id, canned + '\n\nЕщё вопрос? Спрашивай 🙂',
                    reply_markup=kb)
        return

    history.append(ChatMessage('user', user_text))
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    reply = await partner.reply(
        history=history,
        character_name='Tutor',
        character_role='patient English tutor for a Russian speaker',
        personality='clear, concise, encouraging; explains simply and gives one example',
        level=context.user_data.get('tutor_level', 'a2'),
        situation='answering a learner question about English; reply in the '
                  'language of the question, keep it short, add one example',
        user_key=context.user_data.get('user_key'),
    )
    history.append(ChatMessage('assistant', reply))
    context.user_data['tutor_history'] = history[-12:]
    context.user_data['tts_text'] = reply if _is_english(reply) else None
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    rows = []
    if _is_english(reply):
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    if context.user_data.get('lesson_help_return'):
        rows.append([InlineKeyboardButton('↩️ Вернуться к уроку', callback_data='lesson:resume')])
    kb = InlineKeyboardMarkup(rows) if rows else None
    await _send(context, chat_id, f'💬 {reply}', reply_markup=kb)


# --------------------------------------------------------------------------- #
# Paywall / payment
# --------------------------------------------------------------------------- #

async def _show_paywall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = settings.SUBSCRIPTION_PRICE_RUB
    days = settings.SUBSCRIPTION_DAYS
    await _send(
        context, _chat_id(update),
        'Ты прошёл бесплатные уроки — здорово! 👏\n\n'
        f'Дальше — полный доступ на {days} дней:\n'
        '• ежедневные уроки под твой уровень;\n'
        '• словарь с умным повторением;\n'
        '• диалоги и говорение с проверкой AI;\n'
        '• история с Emma и новые серии;\n'
        '• XP, стрики и достижения.\n\n'
        f'Всего {price} ₽ на {days} дней. Без автопродления.',
        reply_markup=keyboards.paywall_kb(price),
    )


async def show_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = settings.SUBSCRIPTION_PRICE_RUB
    days = settings.SUBSCRIPTION_DAYS
    await _send(
        context, _chat_id(update),
        'Условия подписки:\n\n'
        f'• Стоимость: {price} ₽ за {days} дней доступа.\n'
        '• Без автопродления — доступ просто закончится через 30 дней.\n'
        '• Бесплатно: диагностика уровня и 2 пробных урока.\n'
        '• Оплата через ЮKassa (подключается после модерации магазина).\n'
        '• Вопросы по оплате — в поддержку проекта.',
        reply_markup=keyboards.main_menu(),
    )


async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile_id = context.user_data['profile_id']
    chat_id = _chat_id(update)

    if await db.has_active_subscription(profile_id):
        await _send(context, chat_id, 'У тебя уже есть активная подписка ✅',
                    reply_markup=keyboards.main_menu())
        return

    if settings.PAYMENT_MODE == 'mock':
        result = await db.activate_mock_subscription(profile_id)
        await _send(
            context, chat_id,
            'Тестовая оплата прошла ✅\n\n'
            f'Подписка активна до {result["expires_at"]}.\n'
            '(mock-режим — реальную оплату ЮKassa подключим после модерации.)',
            reply_markup=keyboards.main_menu(),
        )
        return

    if not settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN:
        await _send(context, chat_id,
                    'Оплата пока не настроена (нет provider token).',
                    reply_markup=keyboards.main_menu())
        return

    plan = await db.get_or_create_plan()
    prices = [LabeledPrice(label=plan['name'], amount=settings.SUBSCRIPTION_PRICE_KOPEKS)]
    await context.bot.send_invoice(
        chat_id=chat_id,
        title='English Mentor — доступ на 30 дней',
        description='Полный доступ к урокам, словарю и практике на 30 дней.',
        payload=f'sub:{profile_id}',
        provider_token=settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN,
        currency='RUB',
        prices=prices,
        start_parameter='english-mentor-sub',
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_profile(update, context)
    result = await db.activate_mock_subscription(context.user_data['profile_id'])
    await _send(context, _chat_id(update),
                f'Оплата прошла ✅ Подписка активна до {result["expires_at"]}.',
                reply_markup=keyboards.main_menu())


# --------------------------------------------------------------------------- #
# Routers
# --------------------------------------------------------------------------- #

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await _ensure_profile(update, context)
    data = query.data or ''

    if data == 'diag:start':
        await _begin_diagnostic(update, context)
    elif data.startswith('diag:opt:'):
        idx = int(data.rsplit(':', 1)[1])
        diag = context.user_data.get('diag') or {}
        item = diag.get('current') or {}
        options = item.get('options', [])
        if idx < len(options):
            await _handle_diagnostic_answer(update, context, options[idx])
    elif data == 'tts:step':
        step = context.user_data.get('current_step')
        speak = _speak_text_for_step(step) if step else None
        if speak:
            await _send_tts(context, _chat_id(update), speak)
    elif data == 'tts:dict':
        speak = context.user_data.get('dict_speak')
        if speak:
            await _send_tts(context, _chat_id(update), speak)
    elif data == 'tts:say':
        speak = context.user_data.get('tts_text')
        if speak:
            await _send_tts(context, _chat_id(update), speak)
    elif data == 'nav:menu':
        context.user_data['mode'] = None
        context.user_data['expect'] = None
        await _send(context, _chat_id(update), 'Главное меню 👇',
                    reply_markup=keyboards.main_menu())
    elif data == 'lesson:next':
        await _advance(update, context)
    elif data == 'lesson:ask':
        step = context.user_data.get('current_step') or {}
        speak = _speak_text_for_step(step)
        if speak:
            context.user_data['tts_text'] = speak
        context.user_data['lesson_help_return'] = True
        context.user_data['mode'] = 'tutor'
        hint = (step.get('title') or step.get('text') or '')[:180]
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await _send(
            context, _chat_id(update),
            '💬 Задай вопрос по этому шагу — текстом или голосом 🎙️'
            + (f'\n\n<i>{_esc(hint)}</i>' if hint else ''),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('↩️ Вернуться к уроку', callback_data='lesson:resume'),
            ]]),
            parse_mode=ParseMode.HTML,
        )
    elif data == 'lesson:resume':
        context.user_data['mode'] = 'lesson'
        context.user_data.pop('lesson_help_return', None)
        await _send(context, _chat_id(update), 'Продолжаем урок 👇')
    elif data.startswith('lesson:open:'):
        await open_lesson(update, context, int(data.rsplit(':', 1)[1]))
    elif data == 'ex:hint':
        await query.answer()
        await _show_exercise_hint(update, context)
    elif data.startswith('ex:opt:'):
        idx = int(data.rsplit(':', 1)[1])
        if context.user_data.get('mode') == 'rule_drill':
            await _handle_rule_drill_choice(update, context, idx)
        else:
            await _handle_exercise_choice(update, context, idx)
    elif data == 'plan:back':
        plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
            context.user_data['profile_id'],
        )
        await _mark_plan_item_by_type(context.user_data['profile_id'], plan, 'warmup')
        await show_daily_plan(update, context)
    elif data == 'plan:continue':
        await _plan_continue(update, context)
    elif data == 'plan:warmup:next':
        plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
            context.user_data['profile_id'],
        )
        await _mark_plan_item_by_type(context.user_data['profile_id'], plan, 'warmup')
        plan = await db.get_daily_plan(context.user_data['profile_id'])
        context.user_data['daily_plan'] = plan
        episode = plan.get('episode')
        if episode and not episode.get('done'):
            await open_lesson(
                update, context, episode['lesson_id'],
                plan_block_id=episode['block_id'],
            )
        else:
            await show_daily_plan(update, context)
    elif data == 'plan:menu':
        await show_daily_plan(update, context)
    elif data == 'plan:warmup':
        await _show_warmup(update, context)
    elif data == 'plan:warmup:listen':
        speak = context.user_data.get('tts_text')
        if speak:
            await _send_tts(context, _chat_id(update), speak)
    elif data.startswith('plan:episode:'):
        lesson_id = int(data.rsplit(':', 1)[1])
        plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
            context.user_data['profile_id'],
        )
        block_id = next(
            (i['block_id'] for i in plan.get('items', [])
             if i['type'] == 'episode' and i.get('lesson_id') == lesson_id),
            None,
        )
        await open_lesson(update, context, lesson_id, plan_block_id=block_id)
    elif data == 'plan:words':
        await start_word_review(update, context, from_plan=True)
    elif data == 'plan:rules':
        await start_rule_drill(update, context)
    elif data.startswith('rule:learn:'):
        key = data.split(':', 2)[2]
        await db.set_user_rule_status(context.user_data['profile_id'], key, 'learned')
        await query.answer('✅ Добавлено в библиотеку')
    elif data.startswith('rule:known:'):
        key = data.split(':', 2)[2]
        await db.set_user_rule_status(context.user_data['profile_id'], key, 'known')
        await query.answer('🟢 Отмечено как «уже знаю»')
    elif data == 'rules:map':
        await show_rules_map(update, context)
    elif data.startswith('rules:topic:'):
        idx = int(data.rsplit(':', 1)[1])
        topics = context.user_data.get('rules_topics_map') or {}
        if not topics:
            profile = await _ensure_profile(update, context)
            data_map = await db.get_rules_map(profile['id'])
            topics = data_map.get('topics') or {}
            context.user_data['rules_topics_map'] = topics
        topic_keys = list(topics.keys())
        if idx < 0 or idx >= len(topic_keys):
            await show_rules_map(update, context)
            return
        topic = topic_keys[idx]
        await show_rules_topic(update, context, topic, topics[topic])
    elif data == 'rules:drill':
        await start_rule_drill(update, context)
    elif data.startswith('rules:view:'):
        await show_rule_detail(update, context, data.split(':', 2)[2])
    elif data.startswith('rules:listen:'):
        rule = await db.get_rule_detail(
            context.user_data['profile_id'], data.split(':', 2)[2],
        )
        speak = _grammar_speak_text({
            'table': (rule or {}).get('table', {}),
            'examples': (rule or {}).get('examples', []),
        })
        if speak:
            await _send_tts(context, _chat_id(update), speak)
    elif data == 'rules:noop':
        await query.answer()
    elif data == 'notify:yes':
        await _send(context, _chat_id(update),
                    'Во сколько напоминать? (по Москве) ⏰',
                    reply_markup=keyboards.reminder_time_kb())
    elif data == 'notify:no':
        await db.set_notifications(context.user_data['profile_id'], enabled=False)
        await _send(context, _chat_id(update),
                    'Хорошо. Включить напоминания можно в 👤 Профиль → 🔔',
                    reply_markup=keyboards.main_menu())
    elif data.startswith('notify:time:'):
        t = data.rsplit(':', 1)[1]
        await db.set_notifications(
            context.user_data['profile_id'], enabled=True, time_str=t,
        )
        await _send(
            context, _chat_id(update),
            f'🔔 Готово! Буду напоминать каждый день в {t}.\n'
            'Пришлю факт дня и ссылку на твой план.',
            reply_markup=keyboards.main_menu(),
        )
    elif data == 'profile:notify':
        notify = await db.get_notification_settings(context.user_data['profile_id'])
        status = f'включены в {notify["time"]}' if notify.get('enabled') and notify.get('time') else 'выключены'
        await _send(
            context, _chat_id(update),
            f'Напоминания: {status}.\nВыбери новое время или отключи:',
            reply_markup=keyboards.reminder_time_kb(),
        )
    elif data == 'dialogue:finish':
        await _finish_dialogue(update, context)
    elif data == 'buy':
        await buy_subscription(update, context)
    elif data == 'terms':
        await show_terms(update, context)
    elif data == 'practice:weak':
        await start_weak_practice(update, context)
    elif data.startswith('pr:opt:'):
        await _handle_practice_choice(update, context, int(data.rsplit(':', 1)[1]))
    elif data == 'srs:start':
        await start_word_review(update, context)
    elif data == 'srs:next':
        await _ask_next_word(update, context)
    elif data == 'profile:interests':
        await show_interests(update, context)
    elif data == 'profile:goal':
        await show_goal(update, context)
    elif data == 'profile:rediag':
        await db.reset_diagnostic(context.user_data['profile_id'])
        await _begin_diagnostic(update, context)
    elif data.startswith('intr:toggle:'):
        await db.toggle_interest(context.user_data['profile_id'], int(data.rsplit(':', 1)[1]))
        await _refresh_interests(update, context)
    elif data == 'intr:done':
        if context.user_data.get('onboarding'):
            await _send(context, _chat_id(update), 'Отлично! И последнее 👇')
            await show_sphere(update, context)
        else:
            await _send(context, _chat_id(update), 'Интересы сохранены ✅')
            await show_profile(update, context)
    elif data == 'profile:sphere':
        await show_sphere(update, context)
    elif data.startswith('goal:set:'):
        await db.set_learning_goal(context.user_data['profile_id'], data.rsplit(':', 1)[1])
        if context.user_data.get('onboarding'):
            await _send(context, _chat_id(update), 'Супер! Теперь выбери интересы 👇')
            await show_interests(update, context)
        else:
            await _send(context, _chat_id(update), 'Цель сохранена ✅')
            await show_profile(update, context)
    elif data.startswith('sph:set:'):
        code = data.rsplit(':', 1)[1]
        await db.set_profession(context.user_data['profile_id'], code)
        context.user_data['sphere_en'] = db.SPHERE_EN.get(code, '')
        if context.user_data.pop('onboarding', False):
            await _send(
                context, _chat_id(update),
                'Всё готово! 🎉 Я собрал персональный план под твой уровень, '
                'интересы и сферу.\n\n'
                'Жми «📚 Учиться» — там чеклист на сегодня, без выбора уроков.',
                reply_markup=keyboards.main_menu(),
            )
            notify = await db.get_notification_settings(context.user_data['profile_id'])
            if not notify.get('setup_done'):
                await _prompt_notifications(update, context)
        else:
            await _send(context, _chat_id(update), 'Сфера сохранена ✅')
            await show_profile(update, context)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    await _ensure_profile(update, context)

    menu = {
        keyboards.BTN_LEARN: show_daily_plan,
        keyboards.BTN_PROFILE: show_profile,
        keyboards.BTN_PROGRESS: show_progress,
        keyboards.BTN_WORDS: show_words,
        keyboards.BTN_RULES: show_rules_map,
        keyboards.BTN_TUTOR: start_tutor,
        keyboards.BTN_SUBSCRIBE: _show_paywall,
    }
    if text in menu:
        context.user_data['mode'] = None
        context.user_data['expect'] = None
        await menu[text](update, context)
        return

    mode = context.user_data.get('mode')
    if mode == 'diagnostic':
        await _handle_diagnostic_answer(update, context, text)
        return
    if mode == 'dialogue':
        await _handle_dialogue_turn(update, context, text)
        return
    if mode == 'tutor':
        await _handle_tutor_turn(update, context, text)
        return
    if mode == 'practice' and context.user_data.get('practice_expect') == 'text':
        await _deliver_practice_feedback(update, context, text)
        return
    if mode == 'review':
        await _handle_word_review_answer(update, context, text)
        return
    if mode == 'lesson' and context.user_data.get('expect') in (
        'ex_text', 'ex_voice', 'ex_text_or_voice',
    ):
        await _handle_exercise_text(update, context, text)
        return

    await _send(context, _chat_id(update),
                'Выбери действие в меню 👇', reply_markup=keyboards.main_menu())


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_profile(update, context)
    chat_id = _chat_id(update)

    if not _voice_allowed(context):
        await _send(
            context, chat_id,
            'Сейчас голос не нужен 🙂\n'
            'Голос работает: у наставника 💬, в уроках (задания с 🎙️), '
            'в диалоге с персонажем, в тренировке словаря и на диагностике.',
        )
        return

    voice = update.message.voice
    mode = context.user_data.get('mode')
    if voice and voice.duration < 1 and mode != 'review':
        await _send(
            context, chat_id,
            'Запись слишком короткая 🎙️\n'
            'Скажи чуть дольше (1–2 секунды) или напиши текстом.',
        )
        return

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    langs = _stt_langs_for_context(context)
    transcript_text = await _transcribe_voice(update, context, langs=langs)

    if transcript_text:
        lang_note = ''
        if context.user_data.get('mode') in ('lesson', 'review', 'dialogue'):
            lang_note = ' (EN)'
        await _send(context, chat_id, f'🎙️ Услышал{lang_note}: «{transcript_text}»')
    else:
        extra = ''
        if mode == 'review':
            extra = '\n\nНапиши слово текстом ✍️ или скажи голосом 🎙️ (1–2 сек).'
        elif mode in ('lesson',):
            extra = '\n\nГовори по-английски чётко, 2–3 секунды.'
        await _send(
            context, chat_id,
            'Не удалось распознать голос 😕\n'
            'Попробуй ещё раз или напиши текстом.'
            + extra
            + '\n(Если повторяется — проверь YANDEX_SPEECHKIT_API_KEY в .env)',
        )
        return

    mode = context.user_data.get('mode')
    if mode == 'diagnostic':
        await _handle_diagnostic_answer(update, context, transcript_text)
    elif mode == 'dialogue':
        await _handle_dialogue_turn(update, context, transcript_text)
    elif mode == 'tutor':
        await _handle_tutor_turn(update, context, transcript_text)
    elif mode == 'review':
        await _handle_word_review_answer(update, context, transcript_text)
    elif mode == 'practice':
        await _deliver_practice_feedback(update, context, transcript_text)
    else:
        await _handle_exercise_text(update, context, transcript_text, is_voice=True)


# --------------------------------------------------------------------------- #
# Application factory
# --------------------------------------------------------------------------- #

async def _post_init(app):
    """Register the command menu (the '/' button in Telegram)."""
    await app.bot.set_my_commands([
        BotCommand('start', 'Начало и меню'),
        BotCommand('lessons', 'Уроки под твой уровень'),
        BotCommand('profile', 'Профиль и достижения'),
        BotCommand('tutor', 'Спросить наставника'),
        BotCommand('diagnostic', 'Пройти диагностику заново'),
        BotCommand('help', 'Что я умею'),
    ])


def build_application():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is empty. Add it to .env')

    from telegram.request import HTTPXRequest

    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    app = ApplicationBuilder().token(token).request(request).post_init(_post_init).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('diagnostic', diagnostic_command))
    app.add_handler(CommandHandler('profile', profile_command))
    app.add_handler(CommandHandler('lessons', lessons_command))
    app.add_handler(CommandHandler('plan', plan_command))
    app.add_handler(CommandHandler('tutor', tutor_command))

    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    return app
