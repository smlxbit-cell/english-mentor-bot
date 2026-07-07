"""Telegram bot: onboarding, adaptive diagnostic, interactive lessons
(with media, voice and AI checking), gamification and subscription paywall.

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
    is_garbage_transcript,
    normalize,
    score_speaking,
    score_word_review,
    tutor,
)
from ai_app.speech import get_stt_provider, get_tutor_stt_provider
from ai_app.speech.bilingual import (
    english_portion_for_tutor,
    is_code_switch_message,
    merge_tutor_transcripts,
    merge_whisper_tutor_transcript,
    prepare_tutor_voice_transcript,
    tutor_transcript_label,
)
from ai_app.services.rule_hints import (
    reply_has_substantive_grammar_mistakes,
    strip_rule_tags,
    suggest_rule_keys,
)
from ai_app.services.spirit_character import (
    is_spirit_chat_turn,
    is_spirit_fulfillment_turn,
    spirit_fulfillment_kind,
)
from ai_app.services.tutor_context import (
    extract_grammar_followup_target,
    is_grammar_followup_turn,
)
from ai_app.tts import get_tts_provider

from . import db, keyboards
from . import diagnostic_flow as diag_flow
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

MAX_DIAGNOSTIC_QUESTIONS = diag_flow.PRIMARY_QUESTIONS

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
    context.user_data['personalization_topic'] = profile.get('personalization_topic', '')
    return profile


def _practice_topic(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get('personalization_topic') or context.user_data.get('sphere_en') or ''


_ONBOARDING_PROMPTS = {
    'goal': 'Осталось настроить профиль. Сначала — зачем тебе английский 👇',
    'interests': 'Теперь интересы — от них зависят темы уроков и историй 👇',
    'sphere': 'И последнее — твоя сфера работы или учёбы 👇',
    'schedule': 'Сколько времени готов уделять английскому в день? 👇',
}


async def _resume_onboarding_if_needed(
    update: Update, context: ContextTypes.DEFAULT_TYPE, profile: dict | None = None,
) -> bool:
    """Redirect to the missing onboarding step. Returns True if blocked."""
    profile = profile or await _ensure_profile(update, context)
    if profile.get('onboarding_complete'):
        return False
    step = profile.get('onboarding_step', 'goal')
    if step == 'diagnostic':
        return False
    context.user_data['onboarding'] = True
    prompt = _ONBOARDING_PROMPTS.get(step, 'Давай донастроим профиль 👇')
    await _send(context, _chat_id(update), prompt)
    if step == 'goal':
        await show_goal(update, context)
    elif step == 'interests':
        await show_interests(update, context)
    elif step == 'sphere':
        await show_sphere(update, context)
    elif step == 'schedule':
        await show_schedule_minutes(update, context, onboarding=True)
    return True


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
    """Voice English `text` via TTS. Tries configured provider, then fallbacks."""
    text = (text or '').strip()
    if not text or not settings.TTS_ENABLED:
        return False

    chain: list[str] = []
    primary = (settings.TTS_PROVIDER or 'openai').lower()
    for name in (primary, 'edge', 'openai'):
        if name not in chain:
            chain.append(name)

    for prov_name in chain:
        try:
            provider = get_tts_provider(prov_name)
            if getattr(provider, 'name', '') == 'mock':
                continue
            result = await provider.synthesize(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning('tts failed (%s): %s', prov_name, exc)
            continue
        if not result.ok or not result.audio:
            continue

        bio = io.BytesIO(result.audio)
        bio.name = f'speech.{result.fmt}'
        try:
            if result.fmt == 'ogg':
                await context.bot.send_voice(chat_id, bio)
            else:
                await context.bot.send_audio(chat_id, bio, title='🔊 English')
        except Exception as exc:  # noqa: BLE001
            logger.warning('tts send failed: %s', exc)
            continue
        return True
    return False


async def _play_tts(context, chat_id: int, text: str | None) -> None:
    """Send TTS audio or a short RU notice if synthesis failed."""
    clean = (text or '').strip()
    if not clean:
        clean = _tts_from_tutor_history(context)
    if not clean:
        await _send(context, chat_id, 'Нет текста для озвучки.')
        return
    if not await _send_tts(context, chat_id, clean):
        await _send(
            context, chat_id,
            'Не удалось озвучить 🔊 Попробуй ещё раз через секунду.',
        )


def _is_english(text: str | None) -> bool:
    """True if `text` is predominantly English (so we can safely voice it)."""
    if not text:
        return False
    latin = len(re.findall(r'[A-Za-z]', text))
    cyrillic = len(re.findall(r'[А-Яа-яЁё]', text))
    return latin >= 3 and latin >= cyrillic


def _is_english_enough(text: str | None) -> bool:
    """Relaxed check for short TTS fragments."""
    if not text:
        return False
    latin = len(re.findall(r'[A-Za-z]', text))
    cyrillic = len(re.findall(r'[А-Яа-яЁё]', text))
    return latin >= 2 and latin > cyrillic


def _strip_guillemets(text: str) -> str:
    return re.sub(r'^[«"\'\s]+|[»"\'\s]+$', '', (text or '').strip())


def _normalize_tts_key(text: str) -> str:
    t = _strip_guillemets(re.sub(r'<[^>]+>', '', text or ''))
    return re.sub(r'\s+', ' ', t).strip().lower()


def _extract_english_from_bilingual_line(line: str) -> str:
    """Spirit / lesson line: «English: phrase — «RU»» or «phrase — «RU»»."""
    line = re.sub(r'<[^>]+>', '', line or '').strip()
    if not line:
        return ''
    m = re.match(r'^english:\s*(.+)$', line, re.I)
    body = m.group(1).strip() if m else line
    if '—' in body:
        left, right = body.split('—', 1)
        right = right.strip()
        if re.search(r'[А-Яа-яЁё]', right) or right.startswith('«'):
            body = left.strip()
    if '«' in body:
        body = body.split('«', 1)[0].strip()
    return body.rstrip('.').strip()


def _english_lead_from_mixed_line(line: str) -> str:
    """«EN phrase» — «RU» or EN — «RU» → keep the English lead."""
    line = (line or '').strip()
    if not line:
        return ''
    if '—' in line:
        left = line.split('—', 1)[0].strip()
        if _is_english_enough(left):
            return left.rstrip(':').strip()
    if '«' in line:
        before = line.split('«', 1)[0].strip()
        if before and _is_english_enough(before):
            return before.rstrip(':').strip()
    return line if _is_english_enough(line) else ''


def _english_text_for_tts(reply: str) -> str:
    """Pull English phrase(s) from a tutor reply for the listen button."""
    reply = reply or ''
    plain = re.sub(r'<[^>]+>', '', reply)
    parts: list[str] = []
    seen: set[str] = set()

    def _add(phrase: str) -> None:
        phrase = _strip_guillemets(phrase).strip()
        if not phrase or not _is_english_enough(phrase):
            return
        key = _normalize_tts_key(phrase)
        if key and key not in seen:
            seen.add(key)
            parts.append(phrase)

    if '🇬🇧' in plain:
        for block in plain.split('🇬🇧')[1:]:
            for line in block.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('('):
                    continue
                _add(_extract_english_from_bilingual_line(line))

    for line in plain.split('\n'):
        stripped = line.strip()
        low = stripped.lower()
        if re.match(r'^english:\s*.+[a-z]', stripped, re.I):
            _add(_extract_english_from_bilingual_line(stripped))
            continue
        if any(k in low for k in ('услышал:', 'ещё можно сказать:', 'лучше:', 'грамматика:')):
            tail = stripped.split(':', 1)[-1]
            quoted = re.search(r'«([^»]+)»', tail)
            if quoted and _is_english_enough(quoted.group(1)):
                _add(quoted.group(1))
            else:
                _add(_english_lead_from_mixed_line(tail))

    if not parts:
        for match in re.finditer(r'«([^»]+)»|"([^"]+)"', plain):
            chunk = (match.group(1) or match.group(2) or '').strip()
            _add(chunk)

    if parts:
        return '. '.join(p.rstrip('.').strip() for p in parts[:6])[:800]

    clean = plain.strip()
    return clean if _is_english(clean) else ''


def _tts_from_tutor_history(context) -> str:
    """Recover speakable English from the last tutor reply if tts_text was lost."""
    history = context.user_data.get('tutor_history') or []
    for msg in reversed(history):
        if getattr(msg, 'role', '') == 'assistant':
            text = _english_text_for_tts(getattr(msg, 'content', '') or '')
            if text:
                return text
    return ''


def _restore_tutor_mode_if_active(context, *, voice_turn: bool = False) -> None:
    """Keep mentor mode across turns when session history is still active."""
    if not context.user_data.get('tutor_history'):
        return
    hard_block = {'lesson', 'diagnostic', 'dialogue', 'review', 'practice'}
    if context.user_data.get('mode') in hard_block:
        return
    if voice_turn:
        context.user_data.pop('rule_training', None)
        context.user_data.pop('rule_drill', None)
        context.user_data['expect'] = None
    context.user_data['mode'] = 'tutor'


def _voice_allowed(context) -> bool:
    """True when the current flow accepts a Telegram voice message."""
    mode = context.user_data.get('mode')
    expect = context.user_data.get('expect')
    if context.user_data.get('tutor_history'):
        if mode not in ('lesson', 'diagnostic', 'dialogue', 'review'):
            return True
    if mode in ('diagnostic', 'dialogue', 'tutor', 'review'):
        return True
    if context.user_data.get('lesson_help_return'):
        return True
    if mode == 'rule_drill':
        training = context.user_data.get('rule_training') or {}
        exercises = training.get('exercises') or []
        idx = training.get('index', 0)
        if idx < len(exercises):
            ex = exercises[idx]
            if ex.get('exercise_type') == 'fill_gap' and ex.get('accept_voice'):
                return True
        return False
    if mode == 'practice' and context.user_data.get('practice_expect') == 'text':
        return True
    if mode == 'lesson' and expect in ('ex_voice', 'ex_text_or_voice'):
        return True
    return False


def _clear_tutor_session(context) -> None:
    context.user_data.pop('tutor_history', None)
    context.user_data.pop('lesson_help_return', None)
    context.user_data.pop('tutor_level', None)


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


def _stt_quality_score(text: str) -> int:
    if is_garbage_transcript(text):
        return -1000
    from ai_app.speech.bilingual import looks_like_transliterated_russian
    if looks_like_transliterated_russian(text):
        return -500
    words = re.findall(r'\w+', text, flags=re.UNICODE)
    unique = len({w.lower() for w in words})
    latin = len(re.findall(r'[A-Za-z]', text))
    cyrillic = len(re.findall(r'[А-Яа-яЁё]', text))
    long_words = sum(1 for w in words if len(w) >= 4)
    return unique * 12 + long_words * 5 + len(words) + latin + cyrillic * 3


async def _transcribe_tutor_voice(stt, audio: bytes, *, short: bool) -> str:
    """Transcribe mentor voice — Whisper + Yandex RU/EN passes, then merge."""

    async def _transcribe_one(provider, lang: str) -> str:
        try:
            transcript = await provider.transcribe(audio, lang=lang, short_utterance=short)
            return (transcript.text or '').strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                'Tutor STT failed (%s via %s): %s',
                lang, getattr(provider, 'name', '?'), exc,
            )
            return ''

    ru_text = ''
    en_text = ''

    # Whisper (AITUNNEL) first when configured — best on mixed RU+EN.
    if settings.OPENAI_API_KEY:
        whisper = get_stt_provider('whisper')
        if whisper.name != 'mock':
            ru_text = await _transcribe_one(whisper, 'ru-RU')
            en_text = await _transcribe_one(whisper, 'en-US')

    # Yandex reinforces weak passes (or is primary when Whisper blocked).
    yandex = get_stt_provider('yandex')
    if yandex.name != 'mock':
        ru_is_latin_only = bool(
            ru_text and not re.search(r'[А-Яа-яЁё]', ru_text) and re.search(r'[A-Za-z]', ru_text),
        )
        if ru_is_latin_only:
            ru_text = ''
        if not ru_text or not re.search(r'[А-Яа-яЁё]', ru_text):
            yandex_ru = await _transcribe_one(yandex, 'ru-RU')
            if yandex_ru:
                ru_text = yandex_ru
        if not en_text:
            yandex_en = await _transcribe_one(yandex, 'en-US')
            if yandex_en:
                en_text = yandex_en
        elif getattr(stt, 'name', '') == 'yandex' and not ru_text:
            yandex_ru = await _transcribe_one(yandex, 'ru-RU')
            if yandex_ru:
                ru_text = yandex_ru

    if not ru_text and not en_text and getattr(stt, 'name', '') not in ('mock',):
        ru_text = await _transcribe_one(stt, 'ru-RU')
        en_text = await _transcribe_one(stt, 'en-US')

    merged = merge_tutor_transcripts(ru_text, en_text)
    if merged:
        return merged

    if settings.OPENAI_API_KEY:
        whisper = get_stt_provider('whisper')
        if whisper.name != 'mock':
            auto = await _transcribe_one(whisper, 'auto')
            if auto:
                return merge_whisper_tutor_transcript(auto)

    if yandex.name != 'mock':
        for lang in ('ru-RU', 'en-US'):
            yandex_text = await _transcribe_one(yandex, lang)
            if yandex_text:
                return yandex_text

    return ru_text or en_text

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

    if context.user_data.get('mode') == 'tutor':
        limits = await db.get_user_limits(context.user_data['profile_id'])
        tutor_stt = get_tutor_stt_provider(stt_model=limits.get('stt_model'))
        return await _transcribe_tutor_voice(tutor_stt, audio, short=short)

    best_text = ''
    best_score = -1001
    for lang in langs:
        try:
            transcript = await stt.transcribe(audio, lang=lang, short_utterance=short)
            text = (transcript.text or '').strip()
            if not text:
                continue
            score = _stt_quality_score(text)
            if score > best_score:
                best_score = score
                best_text = text
        except Exception as exc:  # noqa: BLE001
            logger.warning('STT failed (%s): %s', lang, exc)

    if not best_text and settings.STT_YANDEX_FALLBACK and getattr(stt, 'name', '') != 'yandex':
        yandex = get_stt_provider('yandex')
        if yandex.name != 'mock':
            for lang in langs:
                try:
                    transcript = await yandex.transcribe(audio, lang=lang, short_utterance=short)
                    text = (transcript.text or '').strip()
                    if not text:
                        continue
                    score = _stt_quality_score(text)
                    if score > best_score:
                        best_score = score
                        best_text = text
                except Exception as exc:  # noqa: BLE001
                    logger.warning('Yandex STT fallback failed (%s): %s', lang, exc)
    return best_text


def _exercise_accepts_voice(content: dict, etype: str) -> bool:
    if content.get('accept_voice') is False:
        return False
    if content.get('accept_voice') is True:
        return True
    return etype in VOICE_EXERCISE_TYPES


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

    for candidate in (_compose_step_text(step), step.get('text'), step.get('title')):
        if not candidate:
            continue
        extracted = _english_text_for_tts(candidate)
        if extracted:
            return extracted
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
            'Сначала короткая диагностика — подберём программу под твой уровень.',
            reply_markup=keyboards.start_diagnostic_kb(),
        )
        return

    if not profile.get('onboarding_complete'):
        await send_mentor_reaction(context, chat_id, 'welcome_back')
        await _resume_onboarding_if_needed(update, context, profile)
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
    context.user_data['diag'] = {'group': group}
    await send_mentor_reaction(context, chat_id, 'diagnostic_start')
    await _send(
        context, chat_id,
        'Диагностика уровня 🎯\n\n'
        'Как ты оцениваешь свой английский сейчас?',
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.diagnostic_self_assess_kb(),
    )


async def _start_diagnostic_test(
    update: Update, context: ContextTypes.DEFAULT_TYPE, claimed: str,
):
    chat_id = _chat_id(update)
    group = context.user_data['diag']['group']
    min_i, max_i, start_i = diag_flow.test_band(claimed)

    context.user_data['diag'] = {
        'group': group,
        'claimed': claimed,
        'claimed_idx': diag_flow.level_index(claimed),
        'band': (min_i, max_i),
        'asked': [],
        'level_idx': start_i,
        'count': 0,
        'correct': 0,
        'skill': {},
        'skills_used': set(),
        'current': None,
        'challenge': False,
        'challenge_count': 0,
        'challenge_correct': 0,
    }
    await _ask_next_diagnostic(update, context)


def _pick_diagnostic_item(diag: dict):
    item = diag_flow.pick_item(
        diag['group'],
        set(diag['asked']),
        diag['band'],
        diag['level_idx'],
        used_skills=diag.get('skills_used') or set(),
    )
    if item:
        diag.setdefault('skills_used', set()).add(item['skill'])
    return item


def _diag_limit(diag: dict) -> int:
    return (
        diag_flow.CHALLENGE_QUESTIONS if diag.get('challenge')
        else diag_flow.PRIMARY_QUESTIONS
    )


def _diag_progress(diag: dict) -> int:
    if diag.get('challenge'):
        return diag.get('challenge_count', 0)
    return diag.get('count', 0)


async def _ask_next_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diag = context.user_data['diag']
    chat_id = _chat_id(update)
    limit = _diag_limit(diag)

    if _diag_progress(diag) >= limit:
        if diag.get('challenge'):
            diag['phase'] = 'challenge_done'
            await _finish_diagnostic(update, context)
        elif diag_flow.should_offer_challenge({**diag, 'phase': 'primary_done'}):
            diag['phase'] = 'primary_done'
            await send_mentor_reaction(context, chat_id, 'answer_correct')
            await _send(
                context, chat_id,
                'Отлично справляешься! 👍\n\n'
                'Похоже, можешь больше. Проверим посложнее?',
                reply_markup=keyboards.diagnostic_challenge_kb(),
            )
        else:
            await _finish_diagnostic(update, context)
        return

    item = _pick_diagnostic_item(diag)
    if not item:
        await _finish_diagnostic(update, context)
        return

    diag['current'] = item
    diag['asked'].append(item['id'])
    if diag.get('challenge'):
        diag['challenge_count'] = diag.get('challenge_count', 0) + 1
        number = diag['challenge_count']
        total = diag_flow.CHALLENGE_QUESTIONS
    else:
        diag['count'] += 1
        number = diag['count']
        total = diag_flow.PRIMARY_QUESTIONS

    if item['item_type'] == 'listening' and item.get('audio'):
        await _send_media(context, chat_id, item['audio'])

    prompt = f'Вопрос {number}/{total}\n\n{item["prompt"]}'
    task = diag_flow.task_instruction(item)
    if task:
        prompt += f'\n\n{task}'
    listen_text = _english_text_for_tts(item['prompt'])
    listen = bool(listen_text)
    context.user_data['tts_text'] = listen_text or None
    parse_mode = (
        ParseMode.HTML
        if any(x in item['prompt'] for x in ('<b>', '<i>', '«'))
        else None
    )

    if item['item_type'] in ('multiple_choice', 'listening') and item['options']:
        await _send(
            context, chat_id, prompt,
            reply_markup=keyboards.diagnostic_options_kb(
                item['options'], item_id=item['id'], with_listen=listen,
            ),
            parse_mode=parse_mode,
        )
    elif item['item_type'] == 'speaking':
        await _send(context, chat_id, prompt, parse_mode=parse_mode)
    else:
        await _send(
            context, chat_id, prompt,
            reply_markup=keyboards.say_kb() if listen else None,
            parse_mode=parse_mode,
        )


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


async def _clear_diagnostic_buttons(update: Update) -> None:
    query = update.callback_query
    if not query or not query.message:
        return
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:  # noqa: BLE001
        pass


async def _handle_diagnostic_answer(update, context, answer_text: str):
    diag = context.user_data.get('diag')
    if not diag or not diag.get('current'):
        return
    item = diag['current']
    chat_id = _chat_id(update)

    is_correct = await _score_diagnostic_answer(item, answer_text)

    skill = item['skill']
    c, t = diag['skill'].get(skill, [0, 0])
    diag['skill'][skill] = [c + (1 if is_correct else 0), t + 1]

    min_i, max_i = diag['band']
    if is_correct:
        diag['correct'] = diag.get('correct', 0) + 1
        if diag.get('challenge'):
            diag['challenge_correct'] = diag.get('challenge_correct', 0) + 1
        diag['level_idx'] = min(max_i, diag['level_idx'] + 1)
        await send_mentor_reaction(context, chat_id, 'answer_correct')
        feedback = 'Верно! 👍'
    else:
        diag['level_idx'] = max(min_i, diag['level_idx'] - 1)
        await send_mentor_reaction(context, chat_id, 'answer_wrong')
        feedback = 'Не совсем — ничего страшного, идём дальше 🙂'
        tip = (item.get('explanation_ru') or '').strip()
        if tip:
            feedback += f'\n\n💡 {tip}'
        elif item.get('correct'):
            ans = item['correct'][0]
            feedback += (
                f'\n\n💡 Ты выбрал(а): <b>{_esc(answer_text)}</b>\n'
                f'Правильно: <b>{_esc(ans)}</b>'
            )

    diag['current'] = None
    await _clear_diagnostic_buttons(update)
    use_html = bool((item.get('explanation_ru') or '').strip()) or (
        not is_correct and item.get('correct')
    )
    await _send(
        context, chat_id, feedback,
        parse_mode=ParseMode.HTML if use_html else None,
    )
    await _ask_next_diagnostic(update, context)


async def _begin_challenge_round(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diag = context.user_data['diag']
    claimed_idx = diag.get('claimed_idx', 1)
    result_idx = diag.get('level_idx', 1)
    diag['challenge'] = True
    diag['band'] = diag_flow.challenge_band(claimed_idx, result_idx)
    diag['level_idx'] = diag['band'][0]
    diag['challenge_count'] = 0
    diag['challenge_correct'] = 0
    chat_id = _chat_id(update)
    await send_mentor_reaction(context, chat_id, 'lesson_start')
    await _ask_next_diagnostic(update, context)


async def _finish_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diag = context.user_data.get('diag', {})
    chat_id = _chat_id(update)
    level_code = diag_flow.finalize_level(diag)
    claimed = diag.get('claimed', 'unsure')

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
        weak_text = '\n\nНад чем поработаем: ' + ', '.join(
            names.get(s, s) for s in weak
        ) + '.'

    await send_mentor_reaction(context, chat_id, 'diagnostic_done')
    body = diag_flow.result_message(claimed, level_code, diag) + weak_text
    await _send(
        context, chat_id,
        body + '\n\nЕщё пара вопросов, чтобы подобрать уроки именно под тебя 👇',
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.main_menu(),
    )
    context.user_data['onboarding'] = True
    await db.clear_learning_goal(profile_id)
    await show_goal(update, context)


# --------------------------------------------------------------------------- #
# Daily plan (adventure chapter — no lesson picker)
# --------------------------------------------------------------------------- #

def _progress_bar(done: int, total: int) -> str:
    if total <= 0:
        return ''
    filled = round(done / total * 6)
    return '●' * filled + '○' * (6 - filled)


def _progress_bar_percent(percent: int) -> str:
    pct = max(0, min(100, percent))
    filled = round(pct / 100 * 12)
    return '━' * filled + '░' * (12 - filled)


def _format_daily_plan_text(plan: dict) -> str:
    episode = plan.get('episode')
    ep_num = (episode or {}).get('episode_num', 0)
    if plan.get('is_rest_day'):
        header = '🌿 <b>День отдыха</b>'
    else:
        header = '📖 <b>Глава дня</b>'
        if ep_num:
            header += f' · Эпизод {ep_num}'

    lines = [header, _esc(plan.get('greeting', '')), '']

    if plan.get('is_rest_day'):
        lines.append('Сегодня без нового эпизода — только лёгкая разминка (~5 мин).')
        lines.append('Стрик сохранится 🔥')
        lines.append('')

    steps: list[str] = []
    total_mins = plan.get('progress_minutes_total', 0)
    total_xp = 0

    warmup = plan.get('warmup')
    if warmup:
        from study_app.daily_facts import warmup_label
        icon, label = warmup_label(warmup.get('kind', 'fact'))
        mark = '✅' if warmup.get('done') else '○'
        steps.append(f'{mark} {icon} {label} — ~3 мин')

    if episode:
        mark = '✅' if episode.get('done') else '○'
        mins = episode.get('minutes') or 8
        xp = episode.get('xp_reward') or 0
        title = episode.get('subtitle') or episode.get('title', 'Эпизод')
        meta = f'~{mins} мин'
        if xp:
            meta += f' · +{xp} XP'
            total_xp += xp
        steps.append(f'{mark} 📺 {_esc(title)} — {meta}')
    elif not plan.get('has_episode') and not plan.get('is_rest_day'):
        lines.append('🎬 Все эпизоды пройдены — скоро новая глава!')
        lines.append('')

    listening = plan.get('listening')
    if listening:
        mark = '✅' if listening.get('done') else '○'
        lm = listening.get('target_minutes') or listening.get('minutes') or 4
        steps.append(f'{mark} 🎧 {_esc(listening.get("title", "Аудирование"))} — ~{lm} мин')

    bonus = plan.get('bonus_words')
    if bonus:
        mark = '✅' if bonus.get('done') else '○'
        cnt = bonus.get('count', 0)
        est = bonus.get('target_minutes') or max(2, min(cnt, 8))
        steps.append(f'{mark} 🗂 Повторить {cnt} слов — ~{est} мин')

    drill = plan.get('rule_drill')
    if drill:
        mark = '✅' if drill.get('done') else '○'
        steps.append(f'{mark} 📖 Тренировка правил — ~5 мин')

    if steps:
        summary = f'<b>Маршрут на сегодня</b> (~{total_mins} мин'
        if total_xp:
            summary += f' · +{total_xp} XP'
        summary += '):'
        lines.append(summary)
        lines.append('')
        for i, step in enumerate(steps, 1):
            lines.append(f'{i}. {step}')
        lines.append('')

    pct = plan.get('progress_percent', 0)
    done_m = plan.get('progress_minutes_done', 0)
    total_m = plan.get('progress_minutes_total', 1)
    if total_m > 0:
        bar = _progress_bar_percent(pct)
        lines.append(f'{bar}  {pct}%  ·  ~{done_m} из {total_m} мин')
        lines.append('')

    if plan.get('all_done'):
        if plan.get('is_rest_day'):
            lines.append('🌿 Отдых засчитан! Завтра — новая глава.')
        else:
            lines.append('🎉 Глава дня закрыта! Завтра — новое приключение.')
    else:
        cta = plan.get('continue_label') or (
            'Продолжить' if plan.get('progress_done', 0) > 0 else 'Начать'
        )
        lines.append(f'Нажми <b>▶️ {cta}</b> — поведу по шагам, без выбора.')

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

    if await _resume_onboarding_if_needed(update, context, profile):
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

    context.user_data['daily_plan'] = plan
    context.user_data['tts_text'] = warmup.get('fact_en', '')
    from study_app.daily_facts import warmup_label
    icon, label = warmup_label(warmup.get('kind', 'fact'))
    quiz = warmup.get('quiz') or {}
    if not quiz:
        from study_app.warmup_quiz import build_quiz_for_fact
        from django.utils import timezone as tz
        quiz = build_quiz_for_fact(
            {
                'fact_ru': warmup.get('fact_ru', ''),
                'fact_en': warmup.get('fact_en', ''),
                'kind': warmup.get('kind', 'fact'),
            },
            context.user_data['profile_id'],
            tz.localdate(),
        )
        warmup['quiz'] = quiz
    text = (
        f'{icon} <b>{label}</b>\n\n'
        f'{_esc(warmup.get("fact_ru", ""))}\n\n'
        f'🇬🇧 {_esc(warmup.get("fact_en", ""))}\n\n'
        f'<b>Проверим понимание 👇</b>\n'
        f'{_esc(quiz.get("question_ru", "Выбери правильный вариант:"))}'
    )
    await _send(
        context, chat_id, text,
        reply_markup=keyboards.warmup_kb(quiz),
        parse_mode=ParseMode.HTML,
    )


async def _show_listening(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
        context.user_data['profile_id'],
    )
    chat_id = _chat_id(update)
    listening = plan.get('listening')
    if not listening:
        await _plan_continue(update, context)
        return

    context.user_data['daily_plan'] = plan
    lines = listening.get('lines') or []
    en_lines = [ln.get('en', '') for ln in lines if ln.get('en')]
    context.user_data['tts_text'] = ' '.join(en_lines)

    body = [f'🎧 <b>{_esc(listening.get("title", "Аудирование"))}</b>\n']
    for ln in lines:
        body.append(f'🇬🇧 {_esc(ln.get("en", ""))}')
        if ln.get('ru'):
            body.append(f'🇷🇺 {_esc(ln["ru"])}')
        body.append('')
    body.append(f'<b>{_esc(listening.get("question_ru", ""))}</b>')
    await _send(
        context, chat_id, '\n'.join(body),
        reply_markup=keyboards.listening_kb(listening.get('options') or []),
        parse_mode=ParseMode.HTML,
    )


async def _plan_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    plan = await db.get_daily_plan(profile['id'])
    context.user_data['daily_plan'] = plan

    warmup = plan.get('warmup')
    if warmup and not warmup.get('done'):
        await _show_warmup(update, context)
        return

    if plan.get('is_rest_day'):
        await show_daily_plan(update, context)
        return

    episode = plan.get('episode')
    if episode and not episode.get('done'):
        await open_lesson(
            update, context, episode['lesson_id'],
            plan_block_id=episode['block_id'],
        )
        return

    listening = plan.get('listening')
    if listening and not listening.get('done'):
        await _show_listening(update, context)
        return

    bonus = plan.get('bonus_words')
    if bonus and not bonus.get('done'):
        await start_word_review(update, context, from_plan=True)
        return

    drill = plan.get('rule_drill')
    if drill and not drill.get('done'):
        context.user_data['plan_rule_drill_block'] = drill.get('block_id')
        await start_rule_drill(update, context)
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
        'Пришлю интересный факт на двух языках и план на день — '
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


async def _maybe_show_mistake_rule_tablet(
    update, context, rule_keys: list[str], *, chat_id: int,
) -> None:
    if not rule_keys:
        return
    rule_key = rule_keys[0]
    rule = await db.get_rule_detail(context.user_data['profile_id'], rule_key)
    if not rule:
        return
    status = rule.get('status', '')
    header = '📋 <b>Правило по этой теме</b>\n\n'
    if status in ('learned', 'known'):
        header += 'ℹ️ Это правило уже есть в твоей библиотеке — можно повторить или потренировать.\n\n'
    else:
        header += 'ℹ️ Этого правила ещё нет в библиотеке — можешь добавить.\n\n'
    context.user_data['tts_text'] = _grammar_speak_text({
        'table': rule.get('table', {}),
        'examples': rule.get('examples', []),
    }) or ''
    await _send(
        context, chat_id,
        header + _rule_to_html(rule),
        reply_markup=keyboards.mistake_rule_kb(rule_key, status),
        parse_mode=ParseMode.HTML,
    )


async def start_rule_training(
    update: Update, context: ContextTypes.DEFAULT_TYPE, rule_key: str | None = None,
):
    profile_id = context.user_data['profile_id']
    chat_id = _chat_id(update)
    if not rule_key:
        rule_key = await db.get_next_unlearned_rule_key(profile_id)
    if not rule_key:
        await _send(
            context, chat_id,
            'Все правила отмечены — отлично! 🎉 Новые появятся в следующих эпизодах.',
            reply_markup=keyboards.main_menu(),
        )
        return
    session = await db.get_rule_training(rule_key)
    if not session:
        await _send(context, chat_id, 'Для этого правила тренировка пока не готова.')
        return
    context.user_data['mode'] = 'rule_drill'
    context.user_data['rule_training'] = {
        'rule_key': session['rule_key'],
        'rule_title': session['rule_title'],
        'exercises': session['exercises'],
        'index': 0,
        'score': 0,
    }
    context.user_data.pop('rule_drill', None)
    await _send(
        context, chat_id,
        f'🎯 Тренировка: «{session["rule_title"]}»\n'
        f'Заданий: {len(session["exercises"])}',
    )
    await _show_rule_training_step(update, context)


async def start_rule_drill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_rule_training(update, context, rule_key=None)


async def _show_rule_training_step(update, context):
    training = context.user_data.get('rule_training') or {}
    chat_id = _chat_id(update)
    exercises = training.get('exercises') or []
    idx = training.get('index', 0)
    total = len(exercises)
    if idx >= total:
        await _finish_rule_training(update, context)
        return
    ex = exercises[idx]
    etype = ex.get('exercise_type', 'multiple_choice')
    header = f'🎯 ({idx + 1}/{total})\n\n{ex.get("prompt_ru", "")}'
    if etype == 'multiple_choice':
        context.user_data['expect'] = 'rule_mc'
        await _send(
            context, chat_id, header,
            reply_markup=keyboards.exercise_options_kb(
                ex.get('options', []), with_hint=False, with_ask=False,
            ),
        )
    else:
        context.user_data['expect'] = 'rule_text'
        await _send(context, chat_id, header + '\n\n✍️ Напиши ответ текстом или 🎙️ голосом.')


async def _finish_rule_training(update, context):
    training = context.user_data.get('rule_training') or {}
    chat_id = _chat_id(update)
    score = training.get('score', 0)
    total = len(training.get('exercises') or [])
    rule_key = training.get('rule_key', '')
    if score >= max(1, total - 1):
        await db.set_user_rule_status(
            context.user_data['profile_id'], rule_key, 'learned',
        )
        msg = f'✅ Отлично! {score}/{total} — правило в библиотеке.'
    else:
        msg = f'📊 Результат: {score}/{total}. Повтори правило в 📖 Правила.'
    context.user_data['mode'] = None
    context.user_data['expect'] = None
    context.user_data.pop('rule_training', None)
    block_id = context.user_data.pop('plan_rule_drill_block', None)
    if block_id:
        await db.mark_plan_block_done(context.user_data['profile_id'], block_id)
        plan = await db.get_daily_plan(context.user_data['profile_id'])
        context.user_data['daily_plan'] = plan
        if plan.get('all_done'):
            await _send(context, chat_id, msg + '\n\n🎉 Глава дня закрыта!')
            await show_daily_plan(update, context)
            return
        await _send(context, chat_id, msg)
        await _plan_continue(update, context)
        return
    await _send(context, chat_id, msg, reply_markup=keyboards.main_menu())


async def _grade_rule_training_answer(update, context, answer: str) -> None:
    training = context.user_data.get('rule_training') or {}
    chat_id = _chat_id(update)
    exercises = training.get('exercises') or []
    idx = training.get('index', 0)
    if idx >= len(exercises):
        return
    ex = exercises[idx]
    etype = ex.get('exercise_type', 'multiple_choice')
    result = await checker.check(
        exercise_type=etype,
        user_answer=answer,
        correct=ex.get('correct', []),
        keywords=ex.get('keywords'),
    )
    if result.is_correct:
        training['score'] = training.get('score', 0) + 1
        feedback = '✅ Верно!'
    else:
        correction = ex.get('correct', [''])[0]
        feedback = f'❌ Правильно: {correction}'
    training['index'] = idx + 1
    context.user_data['rule_training'] = training
    await _send(context, chat_id, feedback)
    await _show_rule_training_step(update, context)


async def _handle_rule_drill_choice(update, context, option_index: int):
    training = context.user_data.get('rule_training')
    if training:
        exercises = training.get('exercises') or []
        idx = training.get('index', 0)
        if idx >= len(exercises):
            return
        ex = exercises[idx]
        options = ex.get('options', [])
        if option_index >= len(options):
            return
        await _grade_rule_training_answer(update, context, options[option_index])
        return

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

# --------------------------------------------------------------------------- #
# Lessons: menu + engine
# --------------------------------------------------------------------------- #

async def show_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy lesson list — redirects to the daily plan."""
    await show_daily_plan(update, context)


async def open_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE, lesson_id: int,
                      *, plan_block_id: int | None = None):
    profile = await _ensure_profile(update, context)
    profile_id = profile['id']
    chat_id = _chat_id(update)

    if await _resume_onboarding_if_needed(update, context, profile):
        return

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


# Step types that auto-send English voiceover when the step is shown.
_AUTO_VOICE_STEP_TYPES = frozenset({
    'hook', 'story', 'dialogue', 'vocabulary', 'grammar_note', 'audio',
})


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
            topic = _practice_topic(context)
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
            prompt_speak = _english_text_for_tts(prompt)
            if prompt_speak:
                context.user_data['tts_text'] = prompt_speak
            kb = keyboards.exercise_text_kb(
                with_hint=has_hint,
                with_ask=True,
                with_listen=bool(prompt_speak),
            )
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
        if speak_text:
            await _send_tts(context, chat_id, speak_text)
        return

    # ---- Content steps ------------------------------------------------- #
    speak_text = _speak_text_for_step(step)
    if speak_text:
        context.user_data['tts_text'] = speak_text

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

    if speak_text and stype in _AUTO_VOICE_STEP_TYPES:
        if stype != 'audio' or not step.get('media'):
            await _send_tts(context, chat_id, speak_text)


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
        topic=_practice_topic(context),
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
    if d['premium'] and d.get('subscription_until'):
        sub = (
            f'{d["plan_name"]} — активна до {d["subscription_until"]}\n'
            f'   🎙️ Голос: ~{d["voice_remaining_minutes"]} мин осталось '
            f'(пакет {d["voice_minutes_monthly"]} мин/мес)\n'
            f'   💬 Наставник: ~{d["tutor_messages_remaining"]} вопросов '
            f'осталось в этом месяце'
        )
    elif d['premium']:
        sub = (
            f'{d["plan_name"]}\n'
            f'   🎙️ Голос: ~{d["voice_remaining_minutes"]} мин осталось\n'
            f'   💬 Наставник: ~{d["tutor_messages_remaining"]} вопросов в месяце'
        )
    else:
        sub = (
            'нет активной (2 пробных урока)\n'
            f'   🎙️ Голос: ~{d["voice_remaining_minutes"]} мин '
            f'(пробный лимит {d["voice_minutes_monthly"]} мин/мес)\n'
            f'   💬 Наставник: ~{d["tutor_messages_remaining"]} вопросов в месяце'
        )
    interests = ', '.join(d['interests']) if d['interests'] else 'не выбраны'
    weak = ', '.join(d['weak_skills_ru']) if d['weak_skills_ru'] else '—'

    text = (
        f'👤 Профиль — {name}\n\n'
        f'🎯 Уровень английского: {d["level"]}\n'
        f'🎓 Цель: {d["goal"] or "не выбрана"}\n'
        f'💼 Сфера: {d.get("sphere") or "не выбрана"}\n'
        f'❤️ Интересы: {interests}\n'
        f'⏱ План: {d.get("daily_minutes", 20)} мин · {d.get("study_days_per_week", 5)} дн/нед\n'
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
    custom = await db.get_interests_custom(profile['id'])
    has_custom = bool(custom.strip())
    await _send(
        context, _chat_id(update),
        'Выбери из списка или напиши свои — от этого зависят темы уроков 👇',
        reply_markup=keyboards.interests_kb(items, selected, has_custom=has_custom),
    )


async def _refresh_interests(update, context):
    profile_id = context.user_data['profile_id']
    items = await db.get_interests()
    selected = set(await db.get_user_interest_ids(profile_id))
    custom = await db.get_interests_custom(profile_id)
    has_custom = bool(custom.strip())
    kb = keyboards.interests_kb(items, selected, has_custom=has_custom)
    query = update.callback_query
    if not query or not query.message:
        return
    try:
        await query.edit_message_reply_markup(reply_markup=kb)
    except Exception:  # noqa: BLE001
        try:
            await query.message.edit_reply_markup(reply_markup=kb)
        except Exception as exc:  # noqa: BLE001
            logger.warning('interests keyboard refresh failed: %s', exc)


async def show_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    goals = db.learning_goal_choices()
    # Fresh onboarding — no pre-selected tick from an old profile value.
    current = '' if context.user_data.get('onboarding') else (profile.get('learning_goal') or '')
    await _send(
        context, _chat_id(update),
        'Зачем тебе английский? Это поможет подобрать темы уроков 👇',
        reply_markup=keyboards.goal_kb(goals, current),
    )


async def _continue_after_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('onboarding'):
        await db.clear_user_interests(context.user_data['profile_id'])
        await _send(context, _chat_id(update), 'Супер! Теперь выбери интересы 👇')
        await show_interests(update, context)
    else:
        await _send(context, _chat_id(update), 'Цель сохранена ✅')
        await show_profile(update, context)


async def _prompt_custom_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expect'] = 'goal_custom'
    await _send(
        context, _chat_id(update),
        'Напиши своими словами, зачем тебе английский ✍️\n'
        'Например: «для работы с иностранными клиентами» или «читаю научные статьи».',
    )


async def show_sphere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    current = '' if context.user_data.get('onboarding') else (profile.get('profession') or '')
    if context.user_data.get('onboarding'):
        text = (
            'В какой сфере ты работаешь или учишься?\n'
            'Выбери из списка или напиши свою — под это подстрою практику 👇'
        )
    else:
        text = (
            'В какой сфере ты работаешь или учишься? '
            'Буду иногда давать практику из твоей области 👇'
        )
    await _send(
        context, _chat_id(update), text,
        reply_markup=keyboards.sphere_kb(db.sphere_choices(), current),
    )


async def _prompt_custom_sphere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expect'] = 'sphere_custom'
    await _send(
        context, _chat_id(update),
        'Напиши своими словами, в какой сфере ты работаешь или учишься ✍️\n'
        'Например: строительство, ветеринария, фриланс',
    )


async def _finish_sphere_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    context.user_data['sphere_en'] = profile.get('sphere_en', '')
    context.user_data['personalization_topic'] = profile.get('personalization_topic', '')
    if context.user_data.get('onboarding'):
        await show_schedule_minutes(update, context, onboarding=True)
    else:
        await _send(context, _chat_id(update), 'Сфера сохранена ✅')
        await show_profile(update, context)


async def show_schedule_minutes(
    update: Update, context: ContextTypes.DEFAULT_TYPE, *, onboarding: bool = False,
):
    context.user_data['schedule_edit'] = not onboarding
    schedule = await db.get_study_schedule(context.user_data['profile_id'])
    selected = schedule.get('daily_minutes', 20)
    text = (
        'Сколько минут в день готов уделять английскому?\n\n'
        'От этого зависит, сколько практики будет в плане.'
    )
    if onboarding:
        text = (
            'Отлично! Теперь подберём нагрузку.\n\n'
            + text
        )
    await _send(
        context, _chat_id(update), text,
        reply_markup=keyboards.schedule_minutes_kb(selected),
    )


async def show_schedule_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = await db.get_study_schedule(context.user_data['profile_id'])
    selected = schedule.get('study_days_per_week', 5)
    await _send(
        context, _chat_id(update),
        'Сколько дней в неделю планируешь заниматься?\n\n'
        '🌿 Воскресенье — лёгкий день отдыха (стрик сохранится).',
        reply_markup=keyboards.schedule_days_kb(selected),
    )


async def _save_schedule_and_finish(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    daily_minutes: int,
    study_days_per_week: int,
):
    profile_id = context.user_data['profile_id']
    await db.set_study_schedule(
        profile_id,
        daily_minutes=daily_minutes,
        study_days_per_week=study_days_per_week,
        rest_weekday=6,
    )
    if context.user_data.pop('onboarding', False):
        await db.complete_onboarding(profile_id)
        await _send(
            context, _chat_id(update),
            f'Всё готово! 🎉 План: <b>{daily_minutes} мин</b> · '
            f'<b>{study_days_per_week} дн/нед</b> · воскресенье — отдых.\n\n'
            'Жми «📚 Учиться» — там твой маршрут на сегодня.',
            reply_markup=keyboards.main_menu(),
            parse_mode=ParseMode.HTML,
        )
        notify = await db.get_notification_settings(profile_id)
        if not notify.get('setup_done'):
            await _prompt_notifications(update, context)
    else:
        await _send(
            context, _chat_id(update),
            f'План обновлён: {daily_minutes} мин · {study_days_per_week} дн/нед ✅',
        )
        await show_profile(update, context)


async def show_schedule_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = await db.get_study_schedule(context.user_data['profile_id'])
    mins = schedule.get('daily_minutes', 20)
    days = schedule.get('study_days_per_week', 5)
    await _send(
        context, _chat_id(update),
        f'⏱ <b>План на день</b>\n\n'
        f'• Время: <b>{mins} мин</b> в день\n'
        f'• Частота: <b>{days} дней</b> в неделю\n'
        f'• Воскресенье — лёгкий день отдыха 🌿',
        reply_markup=keyboards.schedule_edit_kb(),
        parse_mode=ParseMode.HTML,
    )


# --------------------------------------------------------------------------- #
# Ask the tutor (free-form AI help)
# --------------------------------------------------------------------------- #

TUTOR_INTRO = (
    '💬 <b>Спирит на связи</b>\n\n'
    'Привет! Я <b>Spirit</b> — дух английского языка 🌟 Летаю между словами '
    'и помогаю, когда хочется поговорить, спросить или попрактиковаться.\n\n'
    '<b>Что можно:</b>\n'
    '• поболтать — спроси «как дела?», «что ты делал сегодня?» — расскажу историю\n'
    '• говорить или писать по-английски, по-русски или вперемешку 🎙️\n'
    '• забыл слово — скажи по-русски, подскажу по-английски\n'
    '• пришли фразу — мягко поправлю; полезное — в 📖 библиотеку правил\n'
    '• попроси историю, совет, рецепт, цитату — расскажу по-своему 🌟\n\n'
    'Ошибаться нормально. Я рядом — спрашивай текстом или голосом 👇'
)


async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = await _ensure_profile(update, context)
    context.user_data['mode'] = 'tutor'
    context.user_data['tutor_history'] = []
    context.user_data['tutor_level'] = profile.get('level_code', 'a2')
    await send_mentor_reaction(context, _chat_id(update), 'tutor_start')
    await _send(
        context, _chat_id(update),
        TUTOR_INTRO,
        reply_markup=keyboards.main_menu(),
        parse_mode=ParseMode.HTML,
    )


async def _send_tutor_reply(context, chat_id: int, reply: str, *, update=None):
    context.user_data['mode'] = 'tutor'
    tts = _english_text_for_tts(reply)
    context.user_data['tts_text'] = tts or None
    if tts:
        context.user_data['last_tutor_tts'] = tts

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    rows = []
    if context.user_data.get('tts_text') or context.user_data.get('last_tutor_tts'):
        rows.append([InlineKeyboardButton('🔊 Слушать', callback_data='tts:say')])
    if context.user_data.get('lesson_help_return'):
        rows.append([InlineKeyboardButton('↩️ Вернуться к уроку', callback_data='lesson:resume')])
    kb = InlineKeyboardMarkup(rows) if rows else None
    await _send(context, chat_id, reply, reply_markup=kb, parse_mode=ParseMode.HTML)


async def _handle_tutor_turn(update, context, user_text: str, *, from_voice: bool = False):
    chat_id = _chat_id(update)
    context.user_data['mode'] = 'tutor'
    history = context.user_data.get('tutor_history') or []

    if from_voice and is_garbage_transcript(user_text):
        await _send(
            context, chat_id,
            'Плохо расслышал 😕\n'
            'Повтори чуть медленнее — сначала по-русски, потом по-английски.\n'
            'Или напиши текстом.',
        )
        return

    # Canned grammar only for typed questions — STT noise caused false matches.
    canned = None if from_voice else explain_grammar(user_text)
    if canned:
        ok, limit_msg = await db.check_tutor_message(context.user_data['profile_id'])
        if not ok:
            await _send(context, chat_id, limit_msg, reply_markup=keyboards.main_menu())
            return
        history.append(ChatMessage('user', user_text))
        history.append(ChatMessage('assistant', canned))
        context.user_data['tutor_history'] = history[-12:]
        await db.register_tutor_message(context.user_data['profile_id'])
        kb = None
        if context.user_data.get('lesson_help_return'):
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton('↩️ Вернуться к уроку', callback_data='lesson:resume'),
            ]])
        await _send(
            context, chat_id,
            canned + '\n\nЕщё вопрос? Спрашивай 🙂',
            reply_markup=kb,
        )
        return

    check_english = bool(english_portion_for_tutor(user_text, from_voice=from_voice))
    code_switch = is_code_switch_message(user_text)
    grammar_followup = is_grammar_followup_turn(user_text, history)
    followup_target = extract_grammar_followup_target(history) if grammar_followup else ''
    if check_english and not code_switch and not grammar_followup:
        en_norm = english_portion_for_tutor(user_text, from_voice=from_voice)
        if '\n' in user_text:
            ru_part = user_text.split('\n', 1)[0].strip()
            user_text = f'{ru_part}\n{en_norm}' if ru_part else en_norm
        else:
            user_text = en_norm
    history.append(ChatMessage('user', user_text))
    profile_id = context.user_data['profile_id']
    ok, limit_msg = await db.check_tutor_message(profile_id)
    if not ok:
        await _send(context, chat_id, limit_msg, reply_markup=keyboards.main_menu())
        return

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    fulfillment_kind = spirit_fulfillment_kind(user_text) or ''
    spirit_fulfillment = bool(fulfillment_kind) and not grammar_followup
    spirit_chat = (
        (is_spirit_chat_turn(user_text) or spirit_fulfillment) and not grammar_followup
    )
    reply = await tutor.reply(
        history=history,
        level=context.user_data.get('tutor_level', 'a2'),
        check_english=check_english and not grammar_followup,
        from_voice=from_voice,
        code_switch=code_switch,
        spirit_chat=spirit_chat,
        grammar_followup=grammar_followup and bool(followup_target),
        followup_target=followup_target,
        spirit_fulfillment=spirit_fulfillment,
        fulfillment_kind=fulfillment_kind,
    )
    await db.register_tutor_message(profile_id)
    reply, tagged_keys = strip_rule_tags(reply)
    rule_keys = suggest_rule_keys(
        user_text=user_text,
        tutor_reply=reply,
        tagged_keys=tagged_keys,
    )
    history.append(ChatMessage('assistant', reply))
    context.user_data['tutor_history'] = history[-12:]
    await _send_tutor_reply(context, chat_id, reply, update=update)
    if check_english and rule_keys and reply_has_substantive_grammar_mistakes(reply) and not code_switch:
        await _maybe_show_mistake_rule_tablet(
            update, context, rule_keys, chat_id=chat_id,
        )


# --------------------------------------------------------------------------- #
# Paywall / payment
# --------------------------------------------------------------------------- #

async def _show_paywall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from billing_app.plans_catalog import format_subscription_plans_message

    days = settings.SUBSCRIPTION_DAYS
    plans = await db.get_subscription_plans()
    sub_plans = [p for p in plans if p.get('plan_kind') == 'subscription']
    text = format_subscription_plans_message(
        header='Ты прошёл бесплатные уроки — здорово! 👏\n',
        sub_plans=sub_plans,
        days=days,
    )
    await _send(
        context, _chat_id(update),
        text,
        reply_markup=keyboards.paywall_kb(sub_plans),
        parse_mode=ParseMode.HTML,
    )


async def show_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⭐️ Подписка — status or paywall."""
    await _ensure_profile(update, context)
    profile_id = context.user_data['profile_id']
    limits = await db.get_user_limits(profile_id)

    if limits.get('has_subscription'):
        text = (
            f'Тариф: <b>{limits["plan_name"]}</b>\n'
            f'🎙️ Голос: ~{limits["voice_remaining_minutes"]} мин осталось в этом месяце\n'
            f'💬 Наставник: ~{limits["tutor_messages_remaining"]} вопросов '
            f'осталось (пакет на месяц, не сгорает за день)\n\n'
            'Полная программа: план дня, Emma, словарь, правила.\n'
            'Можно докупить +100 мин голоса, если пакет закончился.'
        )
        await _send(
            context, _chat_id(update),
            text,
            reply_markup=keyboards.subscription_kb(
                has_subscription=True,
                voice_remaining=limits.get('voice_remaining_minutes', 0),
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    from billing_app.plans_catalog import format_subscription_plans_message

    days = settings.SUBSCRIPTION_DAYS
    plans = await db.get_subscription_plans()
    sub_plans = [p for p in plans if p.get('plan_kind') == 'subscription']
    text = format_subscription_plans_message(
        header='Тарифы English Mentor 👇\n',
        sub_plans=sub_plans,
        days=days,
    )
    await _send(
        context, _chat_id(update),
        text,
        reply_markup=keyboards.paywall_kb(sub_plans),
        parse_mode=ParseMode.HTML,
    )


async def show_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from billing_app.plans_catalog import TARIFF_INCLUDES_PLAIN

    days = settings.SUBSCRIPTION_DAYS
    plans = await db.get_subscription_plans()
    sub_lines = []
    for plan in plans:
        if plan.get('plan_kind') == 'subscription':
            sub_lines.append(
                f'• {plan["name"]}: {plan["price_rub"]} ₽ / {days} дней — '
                f'{plan.get("voice_minutes_monthly", 0)} мин голоса наставника/мес'
            )
    addon = next((p for p in plans if p.get('code') == 'voice_100'), None)
    addon_line = ''
    if addon:
        addon_line = (
            f'\n• Докупка голоса: +{addon.get("voice_minutes_in_pack", 100)} мин — '
            f'{addon["price_rub"]} ₽ (нужна активная подписка).'
        )
    await _send(
        context, _chat_id(update),
        'Условия подписки:\n\n'
        + '\n'.join(sub_lines)
        + addon_line
        + f'\n\n{TARIFF_INCLUDES_PLAIN}'
        + '\n\n• Без автопродления — доступ заканчивается через 30 дней.\n'
        '• Бесплатно: диагностика уровня и 2 пробных урока.\n'
        '• Оплата через ЮKassa (подключается после модерации магазина).\n'
        '• Вопросы по оплате — в поддержку проекта.',
        reply_markup=keyboards.main_menu(),
    )


async def buy_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    plan_code: str = 'basic',
):
    profile_id = context.user_data['profile_id']
    chat_id = _chat_id(update)

    plan = await db.get_plan_by_code(plan_code)
    if not plan:
        await _send(context, chat_id, 'Тариф не найден. Попробуй позже.',
                    reply_markup=keyboards.main_menu())
        return

    if plan['plan_kind'] == 'voice_addon':
        if not await db.has_active_subscription(profile_id):
            await _send(
                context, chat_id,
                'Докупка минут доступна только с активной подпиской.\n'
                'Сначала оформи Basic, Active или Pro.',
                reply_markup=keyboards.main_menu(),
            )
            return
    elif await db.has_active_subscription(profile_id):
        await _send(context, chat_id, 'У тебя уже есть активная подписка ✅',
                    reply_markup=keyboards.main_menu())
        return

    if settings.PAYMENT_MODE == 'mock':
        result = await db.activate_mock_subscription(profile_id, plan_code)
        if not result.get('ok'):
            await _send(
                context, chat_id,
                'Нужна активная подписка для докупки минут.',
                reply_markup=keyboards.main_menu(),
            )
            return
        if result.get('kind') == 'voice_addon':
            await _send(
                context, chat_id,
                f'Тестовая оплата прошла ✅\n\n'
                f'+{result["minutes_added"]} мин голоса.\n'
                f'Осталось: ~{result["voice_remaining_minutes"]} мин.',
                reply_markup=keyboards.main_menu(),
            )
        else:
            await _send(
                context, chat_id,
                f'Тестовая оплата прошла ✅\n\n'
                f'Тариф <b>{result["plan_name"]}</b> активен до {result["expires_at"]}.\n'
                '(mock-режим — реальную оплату ЮKassa подключим после модерации.)',
                reply_markup=keyboards.main_menu(),
                parse_mode=ParseMode.HTML,
            )
        return

    if not settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN:
        await _send(context, chat_id,
                    'Оплата пока не настроена (нет provider token).',
                    reply_markup=keyboards.main_menu())
        return

    prices = [LabeledPrice(label=plan['name'], amount=plan['price_kopeks'])]
    if plan['plan_kind'] == 'voice_addon':
        payload = f'addon:{profile_id}:{plan_code}'
        title = f'English Mentor — {plan["name"]}'
        description = plan.get('description') or 'Докупка минут голосового наставника.'
    else:
        payload = f'sub:{profile_id}:{plan_code}'
        title = f'English Mentor — {plan["name"]}'
        description = plan.get('description') or f'Подписка на {plan["duration_days"]} дней.'
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN,
        currency='RUB',
        prices=prices,
        start_parameter=f'english-mentor-{plan_code}',
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_profile(update, context)
    profile_id = context.user_data['profile_id']
    payload = (update.message.successful_payment.invoice_payload or '').strip()
    plan_code = 'basic'
    if ':' in payload:
        parts = payload.split(':')
        if len(parts) >= 3 and parts[0] in ('sub', 'addon'):
            plan_code = parts[2]
    result = await db.activate_mock_subscription(profile_id, plan_code)
    if result.get('kind') == 'voice_addon':
        await _send(
            context, _chat_id(update),
            f'Оплата прошла ✅ +{result["minutes_added"]} мин голоса.\n'
            f'Осталось: ~{result["voice_remaining_minutes"]} мин.',
            reply_markup=keyboards.main_menu(),
        )
    else:
        await _send(
            context, _chat_id(update),
            f'Оплата прошла ✅ Тариф {result.get("plan_name", "")} '
            f'активен до {result["expires_at"]}.',
            reply_markup=keyboards.main_menu(),
        )


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
    elif data.startswith('diag:claim:'):
        claimed = data.rsplit(':', 1)[1]
        await _start_diagnostic_test(update, context, claimed)
    elif data == 'diag:challenge:yes':
        await _begin_challenge_round(update, context)
    elif data == 'diag:challenge:no':
        await _finish_diagnostic(update, context)
    elif data.startswith('diag:ans:'):
        parts = data.split(':')
        if len(parts) != 4:
            return
        item_id = int(parts[2])
        idx = int(parts[3])
        diag = context.user_data.get('diag') or {}
        cur = diag.get('current') or {}
        if cur.get('id') != item_id:
            await query.answer(
                'Это прошлый вопрос — смотри последний выше 🙂',
                show_alert=True,
            )
            return
        options = cur.get('options', [])
        if idx < len(options):
            await _handle_diagnostic_answer(update, context, options[idx])
    elif data.startswith('diag:opt:'):
        # Legacy buttons from older messages (before diag:ans:id:idx).
        idx = int(data.rsplit(':', 1)[1])
        diag = context.user_data.get('diag') or {}
        item = diag.get('current') or {}
        options = item.get('options', [])
        if idx < len(options):
            await _handle_diagnostic_answer(update, context, options[idx])
    elif data == 'tts:step':
        step = context.user_data.get('current_step')
        speak = _speak_text_for_step(step) if step else None
        if not speak:
            speak = context.user_data.get('tts_text')
        if speak:
            await _play_tts(context, _chat_id(update), speak)
    elif data == 'tts:dict':
        speak = context.user_data.get('dict_speak')
        if speak:
            await _play_tts(context, _chat_id(update), speak)
    elif data == 'tts:say':
        speak = (
            context.user_data.get('tts_text')
            or context.user_data.get('last_tutor_tts')
            or _tts_from_tutor_history(context)
        )
        await _play_tts(context, _chat_id(update), speak)
    elif data == 'nav:menu':
        context.user_data['mode'] = None
        context.user_data['expect'] = None
        _clear_tutor_session(context)
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
        await show_daily_plan(update, context)
    elif data == 'plan:continue':
        await _plan_continue(update, context)
    elif data.startswith('plan:warmup:ans:'):
        idx = int(data.rsplit(':', 1)[1])
        plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
            context.user_data['profile_id'],
        )
        warmup = plan.get('warmup') or {}
        quiz = warmup.get('quiz') or {}
        correct = quiz.get('correct_index', -1)
        if idx == correct:
            await query.answer('✅ Верно!')
            await _mark_plan_item_by_type(context.user_data['profile_id'], plan, 'warmup')
            plan = await db.get_daily_plan(context.user_data['profile_id'])
            context.user_data['daily_plan'] = plan
            await _plan_continue(update, context)
        else:
            await query.answer('Почти — попробуй ещё раз')
            hint = quiz.get('hint_ru', '')
            if hint:
                await _send(
                    context, _chat_id(update),
                    f'Не совсем. Подсказка: {_esc(hint)}',
                    reply_markup=keyboards.warmup_kb(quiz),
                    parse_mode=ParseMode.HTML,
                )
    elif data == 'plan:warmup:next':
        await query.answer('Сначала ответь на вопрос 👇')
        await _show_warmup(update, context)
    elif data == 'plan:menu':
        await show_daily_plan(update, context)
    elif data == 'plan:warmup':
        await _show_warmup(update, context)
    elif data == 'plan:warmup:listen':
        await _play_tts(context, _chat_id(update), context.user_data.get('tts_text'))
    elif data == 'plan:listening:listen':
        await _play_tts(context, _chat_id(update), context.user_data.get('tts_text'))
    elif data.startswith('plan:listening:ans:'):
        idx = int(data.rsplit(':', 1)[1])
        plan = context.user_data.get('daily_plan') or await db.get_daily_plan(
            context.user_data['profile_id'],
        )
        listening = plan.get('listening') or {}
        correct = listening.get('correct_index', -1)
        if idx == correct:
            await query.answer('✅ Верно!')
            await _mark_plan_item_by_type(context.user_data['profile_id'], plan, 'listening')
            plan = await db.get_daily_plan(context.user_data['profile_id'])
            context.user_data['daily_plan'] = plan
            await _plan_continue(update, context)
        else:
            await query.answer('Попробуй ещё раз')
            await _show_listening(update, context)
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
        await start_rule_training(update, context, rule_key=None)
    elif data.startswith('rules:train:'):
        await start_rule_training(update, context, rule_key=data.split(':', 2)[2])
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
            await _play_tts(context, _chat_id(update), speak)
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
        t = data.removeprefix('notify:time:')
        await db.set_notifications(
            context.user_data['profile_id'], enabled=True, time_str=t,
        )
        await _send(
            context, _chat_id(update),
            f'🔔 Готово! Буду напоминать каждый день в {t} (Москва).\n'
            'Пришлю факт дня и план на день.',
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
        await buy_subscription(update, context, 'basic')
    elif data.startswith('buy:'):
        await buy_subscription(update, context, data.removeprefix('buy:'))
    elif data == 'paywall:plans':
        await _show_paywall(update, context)
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
        try:
            item_id = int(data.rsplit(':', 1)[1])
            await db.toggle_interest(context.user_data['profile_id'], item_id)
            await _refresh_interests(update, context)
        except Exception as exc:  # noqa: BLE001
            logger.exception('interest toggle failed: %s', exc)
            await _send(
                context, _chat_id(update),
                'Не получилось сохранить интерес — нажми ещё раз.',
            )
    elif data == 'intr:custom':
        context.user_data['expect'] = 'interest_custom'
        await _send(
            context, _chat_id(update),
            'Напиши свои интересы через запятую ✍️\n'
            'Например: космос, гитара, вязание, йога',
        )
    elif data == 'intr:done':
        if not await db.has_any_interests(context.user_data['profile_id']):
            await update.callback_query.answer(
                'Выбери хотя бы один интерес или напиши свои',
                show_alert=True,
            )
            return
        if context.user_data.get('onboarding'):
            await db.clear_profession(context.user_data['profile_id'])
            await _send(context, _chat_id(update), 'Отлично! И последнее 👇')
            await show_sphere(update, context)
        else:
            await _send(context, _chat_id(update), 'Интересы сохранены ✅')
            await show_profile(update, context)
    elif data == 'profile:sphere':
        await show_sphere(update, context)
    elif data == 'profile:schedule':
        await show_schedule_settings(update, context)
    elif data == 'profile:schedule:min':
        context.user_data['schedule_edit'] = True
        context.user_data.pop('onboarding', None)
        await show_schedule_minutes(update, context, onboarding=False)
    elif data == 'profile:schedule:days':
        context.user_data['schedule_edit'] = True
        context.user_data.pop('onboarding', None)
        await show_schedule_days(update, context)
    elif data == 'profile:back':
        await show_profile(update, context)
    elif data.startswith('schedule:min:'):
        minutes = int(data.rsplit(':', 1)[1])
        if context.user_data.get('onboarding'):
            context.user_data['pending_schedule_minutes'] = minutes
            await show_schedule_days(update, context)
        elif context.user_data.get('schedule_edit'):
            sched = await db.get_study_schedule(context.user_data['profile_id'])
            await db.set_study_schedule(
                context.user_data['profile_id'],
                daily_minutes=minutes,
                study_days_per_week=sched.get('study_days_per_week', 5),
            )
            await show_schedule_settings(update, context)
        else:
            context.user_data['pending_schedule_minutes'] = minutes
            await show_schedule_days(update, context)
    elif data.startswith('schedule:days:'):
        days = int(data.rsplit(':', 1)[1])
        if context.user_data.get('onboarding') or context.user_data.get('pending_schedule_minutes'):
            minutes = context.user_data.pop('pending_schedule_minutes', 20)
            await _save_schedule_and_finish(
                update, context,
                daily_minutes=minutes,
                study_days_per_week=days,
            )
        else:
            sched = await db.get_study_schedule(context.user_data['profile_id'])
            await db.set_study_schedule(
                context.user_data['profile_id'],
                daily_minutes=sched.get('daily_minutes', 20),
                study_days_per_week=days,
            )
            await show_schedule_settings(update, context)
    elif data.startswith('goal:set:'):
        code = data.rsplit(':', 1)[1]
        if code == 'other':
            await _prompt_custom_goal(update, context)
        else:
            await db.set_learning_goal(context.user_data['profile_id'], code)
            await _continue_after_goal(update, context)
    elif data.startswith('sph:set:'):
        code = data.rsplit(':', 1)[1]
        if code == 'other':
            await _prompt_custom_sphere(update, context)
        else:
            await db.set_profession(context.user_data['profile_id'], code)
            await _finish_sphere_selection(update, context)


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
        keyboards.BTN_SUBSCRIBE: show_subscription,
    }
    if text in menu:
        context.user_data['mode'] = None
        context.user_data['expect'] = None
        if text != keyboards.BTN_TUTOR:
            _clear_tutor_session(context)
        await menu[text](update, context)
        return

    if context.user_data.get('expect') == 'goal_custom':
        if len(text) < 3:
            await _send(
                context, _chat_id(update),
                'Напиши чуть подробнее — хотя бы пару слов 🙂',
            )
            return
        await db.set_learning_goal(
            context.user_data['profile_id'], 'other', text[:200],
        )
        context.user_data['expect'] = None
        await _ensure_profile(update, context)
        await _continue_after_goal(update, context)
        return

    if context.user_data.get('expect') == 'interest_custom':
        parts = [p.strip() for p in text.split(',') if p.strip()]
        if not parts:
            await _send(
                context, _chat_id(update),
                'Напиши хотя бы один интерес через запятую 🙂',
            )
            return
        await db.set_interests_custom(
            context.user_data['profile_id'], text[:500],
        )
        context.user_data['expect'] = None
        await _ensure_profile(update, context)
        preview = ', '.join(parts[:4])
        if len(parts) > 4:
            preview += '…'
        await _send(context, _chat_id(update), f'Записал: {preview} ✅')
        await show_interests(update, context)
        return

    if context.user_data.get('expect') == 'sphere_custom':
        if len(text) < 3:
            await _send(
                context, _chat_id(update),
                'Напиши чуть подробнее — хотя бы пару слов 🙂',
            )
            return
        await db.set_profession(
            context.user_data['profile_id'], 'other', text[:200],
        )
        context.user_data['expect'] = None
        await _finish_sphere_selection(update, context)
        return

    _restore_tutor_mode_if_active(context)
    mode = context.user_data.get('mode')
    if mode == 'rule_drill' and context.user_data.get('expect') == 'rule_text':
        await _grade_rule_training_answer(update, context, text)
        return
    if mode == 'diagnostic':
        await _handle_diagnostic_answer(update, context, text)
        return
    if mode == 'dialogue':
        await _handle_dialogue_turn(update, context, text)
        return
    if mode == 'tutor':
        await _handle_tutor_turn(update, context, text, from_voice=False)
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
    _restore_tutor_mode_if_active(context, voice_turn=True)

    if not _voice_allowed(context):
        await _send(
            context, chat_id,
            'Сессия наставника прервалась (перезапуск или выход из режима).\n'
            'Нажми 💬 Наставник — и продолжим разговор 🎙️\n\n'
            'Голос также работает в уроках (🎙️), диалогах и тренировке словаря.',
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

    if mode == 'tutor' and voice:
        ok, limit_msg = await db.check_voice_usage(
            context.user_data['profile_id'], voice.duration,
        )
        if not ok:
            kb = keyboards.subscription_kb(
                has_subscription=await db.has_active_subscription(
                    context.user_data['profile_id'],
                ),
                voice_remaining=0,
            )
            await _send(context, chat_id, limit_msg, reply_markup=kb)
            return

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    langs = _stt_langs_for_context(context)
    transcript_text = await _transcribe_voice(update, context, langs=langs)

    if transcript_text and is_garbage_transcript(transcript_text):
        await _send(
            context, chat_id,
            'Плохо расслышал 😕\n'
            'Повтори чуть медленнее — сначала по-русски, потом по-английски.\n'
            'Или напиши текстом.',
        )
        return

    if transcript_text and context.user_data.get('mode') == 'tutor':
        transcript_text = prepare_tutor_voice_transcript(transcript_text)

    if transcript_text:
        if context.user_data.get('mode') == 'tutor':
            heard = tutor_transcript_label(transcript_text)
            await _send(context, chat_id, heard)
        else:
            lang_note = ' (EN)' if context.user_data.get('mode') in (
                'lesson', 'review', 'dialogue',
            ) else ''
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
            + '\n(Если повторяется — проверь YANDEX_SPEECHKIT_API_KEY или STT_PROVIDER в .env)',
        )
        return

    mode = context.user_data.get('mode')
    if mode == 'diagnostic':
        await _handle_diagnostic_answer(update, context, transcript_text)
    elif mode == 'dialogue':
        await _handle_dialogue_turn(update, context, transcript_text)
    elif mode == 'tutor':
        if voice:
            await db.record_voice_usage(context.user_data['profile_id'], voice.duration)
        await _handle_tutor_turn(update, context, transcript_text, from_voice=True)
    elif mode == 'rule_drill' and context.user_data.get('expect') == 'rule_text':
        await _grade_rule_training_answer(update, context, transcript_text)
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
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )
    app_builder = (
        ApplicationBuilder()
        .token(token)
        .request(request)
        .get_updates_request(request)
    )
    if settings.TELEGRAM_PROXY:
        app_builder = app_builder.proxy(settings.TELEGRAM_PROXY)
    app = app_builder.post_init(_post_init).build()

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
