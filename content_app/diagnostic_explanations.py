"""Rich grammar breakdowns for diagnostic «Объяснить» (no AI tokens)."""

from __future__ import annotations

import re


def _bilingual(en: str, ru: str) -> str:
    """English example + Russian gloss — helps advanced learners parse nuance."""
    return f'🇬🇧 <i>{en}</i>\n🇷🇺 {ru}'


def context_block(item: dict) -> str:
    """Pull Russian «…» and the English task line into the explanation."""
    prompt = item.get('prompt') or ''
    ru_match = re.search(r'«([^»]+)»', prompt)
    if not ru_match:
        return ''
    ru = ru_match.group(1).strip()
    en_line = ''
    for line in prompt.split('\n'):
        line = line.strip()
        if not line or line.startswith('Вопрос') or line.startswith('🎧'):
            continue
        if re.search(r'[A-Za-z]', line) and ('___' in line or len(line) > 12):
            en_line = line
            break
    if en_line:
        return f'<b>Задание:</b>\n🇷🇺 «{ru}»\n🇬🇧 <i>{en_line}</i>\n'
    return f'<b>Задание:</b> 🇷🇺 «{ru}»\n'


def _correct_set(item: dict) -> set[str]:
    return {(c or '').lower().strip() for c in item.get('correct') or []}


def _c1_inversion_third(item: dict) -> str:
    body = (
        '<b>Грамматика:</b> инверсия в <b>третьем условном</b> (формальный стиль).\n\n'
        + _bilingual(
            'Had I known about the deadline, I would have finished the report sooner.',
            'Если бы я знал(а) о дедлайне, я бы закончил(а) отчёт раньше.',
        )
        + '\n\n'
        'Обычный порядок слов — то же значение:\n'
        + _bilingual(
            'If I had known about the deadline, I would have finished the report sooner.',
            'Если бы я знал(а) о дедлайне, я бы закончил(а) отчёт раньше.',
        )
        + '\n\n'
        '<b>Had I known</b> = If I had known. Вторая часть: <b>would have + V3</b>.'
    )
    notes = {
        'will finish': 'Future — про будущее; здесь сожаление о прошлом → would have finished.',
        'finished': 'Past Simple — без модального would have.',
        'would finish': 'would + V — второе условное; здесь нужно would have + V3.',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _gloss_over(item: dict) -> str:
    body = (
        '<b>Лексика (C1):</b> <b>gloss over</b> = замалчивать, обходить стороной, '
        'не углубляться в трудности.\n\n'
        + _bilingual(
            'The proposal glosses over the practical hurdles.',
            'В предложении замалчивают / не учитывают практические трудности.',
        )
        + '\n\n'
        '<b>while ambitious</b> = хотя и амбициозное (контраст).'
    )
    notes = {
        'It solves every problem': 'Наоборот — gloss over значит не решать, а скрыть проблемы.',
        'It is not ambitious enough': 'while ambitious говорит об обратном — оно как раз амбициозное.',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _loop_in(item: dict) -> str:
    body = (
        '<b>Лексика (C1):</b> <b>loop in</b> = подключить к обсуждению, проинформировать, '
        'вовлечь (разг. деловой англ.).\n\n'
        + _bilingual(
            'We should have looped in the client before signing off.',
            'Нужно было подключить / проинформировать клиента до финального согласования.',
        )
        + '\n\n'
        '<b>should have + V3</b> = сожаление: «следовало бы было сделать (но не сделали)».'
    )
    notes = {
        'The client signed the contract': 'sign off ≠ подписать контракт с клиентом; речь о согласовании.',
        'The client was on the call': 'loop in — про вовлечение заранее, а не факт звонка.',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _express_concern(item: dict) -> str:
    return (
        '<b>Лексика (C1):</b> формальное письмо.\n\n'
        + _bilingual(
            'I am writing to express my concern about the delay.',
            'Пишу, чтобы выразить обеспокоенность по поводу задержки.',
        )
        + '\n\n'
        'Устойчиво: <b>express / raise / voice concern</b> = выразить обеспокоенность.'
    )


def _wrong_options(item: dict) -> list[str]:
    correct = _correct_set(item)
    return [o for o in (item.get('options') or []) if o.lower().strip() not in correct]


def _option_section(item: dict, notes: dict[str, str]) -> str:
    wrong = _wrong_options(item)
    if not wrong:
        return ''
    lines = ['<b>Почему не другие варианты:</b>']
    for opt in wrong:
        note = notes.get(opt) or notes.get(opt.lower()) or ''
        if note:
            lines.append(f'❌ <b>{opt}</b> — {note}')
    return '\n'.join(lines) if len(lines) > 1 else ''


def _despite(item: dict) -> str:
    body = (
        '<b>Грамматика:</b> <b>Despite</b> = «несмотря на». '
        'После <b>despite</b> ставят <b>существительное</b> (или местоимение + сущ.), '
        'а не прилагательное и не глагол.\n\n'
        '✅ <b>the rain</b> — «дождь» (существительное). '
        'Артикль <b>the</b> часто ставят с погодой, когда говорим о конкретной ситуации '
        '(сейчас идёт / был дождь).\n'
        '✅ <b>rain</b> — тоже верно: <b>despite rain</b> (неисчисляемое сущ. без артикля).\n\n'
        'Если нужен <b>глагол</b>, вместо despite используют <b>although / though</b>:\n'
        'Although it <b>was raining</b>, we went for a walk.'
    )
    notes = {
        'rainy': (
            '«дождливый» — это <b>прилагательное</b>. '
            'После despite нужно сущ.: Despite <b>the rain</b>, не Despite rainy.'
        ),
        'raining': (
            '«идёт дождь» — форма глагола (<b>-ing</b>). '
            'Despite не сочетается с глаголом. Нужно сущ. или although + предложение.'
        ),
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _look_forward(item: dict) -> str:
    body = (
        '<b>Грамматика:</b> устойчивое <b>look forward to</b> = «с нетерпением ждать».\n'
        'Здесь <b>to</b> — <b>предлог</b>, не часть инфинитива, поэтому после него <b>-ing</b>:\n'
        '✅ I look forward to <b>seeing</b> you soon.\n\n'
        'Так же: look forward to <b>meeting</b>, <b>hearing</b> from you.'
    )
    notes = {
        'see': 'голая форма глагола — после предлога to нужен <b>-ing</b>: to seeing.',
        'saw': 'прошедшее время — здесь не подходит; нужна форма <b>-ing</b>.',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _suggest(item: dict) -> str:
    body = (
        '<b>Грамматика:</b> после <b>suggest</b> в разговорном английском обычно идёт '
        '<b>-ing</b> (герундий):\n'
        '✅ She suggested <b>leaving</b> earlier.\n\n'
        'Реже встречается <b>suggest + to-infinitive</b>, но в тесте лучший ответ — <b>leaving</b>.'
    )
    notes = {
        'leave': 'голая форма глагола — после suggest так не говорят.',
        'to leave': 'иногда возможно, но <b>leaving</b> — самый естественный вариант.',
        'left': 'прошедшее время — грамматически не подходит к suggested ___ earlier.',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _second_conditional(item: dict) -> str:
    body = (
        '<b>Грамматика:</b> второе условное — нереальная ситуация <b>сейчас</b>:\n'
        '<b>If + Past Simple</b>, <b>would + глагол</b>\n'
        '✅ If I <b>had</b> more time, I <b>would</b> travel.\n\n'
        '«Если бы у меня было больше времени (сейчас), я бы путешествовал» — '
        'но на самом деле времени мало.'
    )
    notes = {
        'have': 'настоящее время — для нереального «если бы» нужен Past: <b>had</b>.',
        'has': 'форма для he/she/it; с <b>I</b> не сочетается.',
        'will have': 'будущее — не подходит к шаблону If … would …',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _since_for(item: dict) -> str:
    body = (
        '<b>Грамматика:</b> Present Perfect + точка начала:\n'
        '✅ I\'ve lived here <b>since</b> 2010. — «с 2010 года» (когда началось).\n'
        '✅ I\'ve lived here <b>for</b> 5 years. — «в течение 5 лет» (длительность).\n\n'
        'После <b>since</b> — дата/момент; после <b>for</b> — период.'
    )
    notes = {
        'for': 'for + длительность (for 5 years), а здесь конкретный год — нужен <b>since</b>.',
        'from': 'from не используют в этой конструкции с Present Perfect так же, как since.',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _past_perfect_gap(item: dict) -> str:
    return (
        '<b>Грамматика:</b> Past Perfect — действие <b>раньше</b> другого в прошлом:\n'
        '✅ By the time we arrived, the film <b>had</b> already started.\n\n'
        'Сначала начался фильм → потом мы приехали. '
        'Для «более раннего» прошлого используют <b>had + V3</b> (had started).'
    )


def _third_conditional(item: dict) -> str:
    body = (
        '<b>Грамматика:</b> третье условное — сожаление о <b>прошлом</b>:\n'
        'If I <b>had known</b> earlier, I <b>would have told</b> you.\n'
        '✅ If I <b>had</b> known… — «если бы я знал(а)» (но не знал).'
    )
    notes = {
        'have': 'настоящее — для прошлого нереального условия нужен <b>had</b>.',
        'would': 'would ставят во второй части, не в придаточном if.',
        'was': 'was known — пассив; здесь актив: If I had known.',
    }
    extra = _option_section(item, notes)
    return f'{body}\n\n{extra}' if extra else body


def _to_be(item: dict, subject: str, form: str) -> str:
    others = _wrong_options(item)
    if not others:
        return f'С <b>{subject}</b> глагол <b>to be</b> — <b>{form}</b>.'
    lines = [
        f'<b>Грамматика:</b> местоимение <b>{subject}</b> → форма <b>{form}</b> (to be).',
        '',
        '<b>Почему не другие варианты:</b>',
    ]
    for opt in others:
        lines.append(f'❌ <b>{opt}</b> — для <b>{subject}</b> не подходит.')
    return '\n'.join(lines)


def _present_simple_s(item: dict, subject: str) -> str:
    return _to_be(item, subject, 'is') if subject in ('she', 'he', 'it') else ''


def diagnostic_deep_dive(item: dict) -> str:
    """Return a detailed Russian grammar breakdown, or '' if none."""
    p = (item.get('prompt') or '').lower()

    if 'had i known' in p and 'would have' in p:
        return _c1_inversion_third(item)
    if 'glosses over' in p or 'gloss over' in p:
        return _gloss_over(item)
    if 'looped in' in p or 'loop in' in p:
        return _loop_in(item)
    if 'express my concern' in p or 'express my concern about' in p:
        return _express_concern(item)
    if 'hardly' in p and 'when' in p:
        return (
            '<b>Грамматика (C1):</b> конструкция <b>Hardly had … when</b> = «едва … как».\n\n'
            + _bilingual(
                'Hardly had the meeting started when the fire alarm went off.',
                'Едва началось собрание, как сработала пожарная сигнализация.',
            )
            + '\n\n'
            'После Hardly идёт инверсия: <b>had + подлежащее + V3</b>.'
        )
    if 'despite' in p and '___' in p:
        return _despite(item)
    if 'look forward to' in p:
        return _look_forward(item)
    if 'suggested' in p and '___' in p:
        return _suggest(item)
    if 'if i' in p and ('would travel' in p or 'would have' in p or 'had known' in p):
        if 'had known' in p or 'would have told' in p:
            return _third_conditional(item)
        return _second_conditional(item)
    if 'if i ___ more time' in p.replace('\n', ' '):
        return _second_conditional(item)
    if 'lived here' in p and '2010' in p:
        return _since_for(item)
    if 'by the time we arrived' in p:
        return _past_perfect_gap(item)
    if 'i ___ a student' in p:
        return _to_be(item, 'I', 'am')
    if 'she ___ happy' in p:
        return _to_be(item, 'she', 'is')
    if 'she ___ coffee every morning' in p:
        body = (
            '<b>Грамматика:</b> Present Simple, 3-е лицо (she/he/it) → глагол + <b>-s</b>:\n'
            '✅ She <b>drinks</b> coffee every morning.'
        )
        notes = {
            'drink': 'без -s — форма для I/you/we/they.',
            'drinking': '-ing — длительное время или после других конструкций, не здесь.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body
    if 'they ___ to work' in p:
        body = '<b>Грамматика:</b> they → глагол <b>без -s</b>: They <b>go</b> to work.'
        notes = {
            'goes': 'goes — только для she/he/it.',
            'going': 'форму -ing здесь не ставят.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body
    if 'i ___ there yesterday' in p:
        body = '<b>Грамматика:</b> вчера → Past Simple: <b>I wasn\'t</b> there yesterday.'
        notes = {
            "weren't": 'were — для you/we/they, не для I.',
            "didn't": 'didn\'t + глагол — другая конструкция отрицания.',
            "haven't": 'Present Perfect — не сочетается с yesterday.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body
    if 'he said he' in p and 'finished' in p:
        body = (
            '<b>Грамматика:</b> косвенная речь: если в главном Past (said), '
            'в придаточном часто Past Perfect:\n'
            '✅ He said he <b>had</b> already finished.'
        )
        notes = {
            'has': 'Present Perfect — сдвиг времени назад: had finished.',
            'have': 'не согласуется с he.',
            'was': 'was finished — пассив; здесь актив: had finished.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body
    if 'take responsibility' in p or 'responsibility for' in p:
        body = 'Устойчивое сочетание: <b>take responsibility</b> = взять ответственность.'
        notes = {
            'made': 'make responsibility — так не говорят.',
            'did': 'did responsibility — неверный глагол.',
            'got': 'get responsibility — другое значение.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body
    if 'would like a cup of coffee' in p or 'чашку кофе' in p:
        body = (
            '<b>Грамматика:</b> вежливая просьба — <b>I would like…</b>\n'
            '✅ I would like a cup of coffee.\n'
            '❌ I am like… — «like» здесь не «нравиться» в этой конструкции.\n'
            '❌ I would liking… — после would нужен инфинитив без -ing.'
        )
        notes = {
            'I am like a cup of coffee': 'неверная конструкция (похоже на «я похож на…»).',
            'I would liking coffee': 'после would — базовая форма глагола: would like.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body
    if 'has already finished' in p or 'present perfect' in p:
        body = (
            '<b>Грамматика:</b> <b>has/have + V3</b> = Present Perfect.\n'
            '✅ She <b>has already finished</b> — результат уже есть.\n'
            'Past Simple (finished yesterday) — про законченный момент в прошлом.'
        )
        notes = {
            'Past Simple': 'Past Simple — когда есть ясный момент в прошлом (yesterday).',
            'Future': 'Future — про будущее; already здесь не про будущее.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body
    if 'i wish i spoke' in p:
        return (
            '<b>Грамматика:</b> <b>I wish + Past Simple</b> = сожаление о настоящем.\n'
            '✅ I wish I <b>spoke</b> English fluently — хотел бы говорить свободно (сейчас не так).\n'
            'Это не про прошлое событие, а про желание изменить текущую ситуацию.'
        )
    if 'corroborate' in p:
        body = (
            '<b>Лексика (C1):</b> <b>corroborate</b> = подтверждать (факты, гипотезу).\n'
            'The findings corroborate our hypothesis.'
        )
        notes = {
            'confuse': 'confuse = путать.',
            'consist': 'consist (of) = состоять из.',
            'complain': 'complain = жаловаться.',
        }
        extra = _option_section(item, notes)
        return f'{body}\n\n{extra}' if extra else body

    # Vocabulary MC: show translations for all options
    options = item.get('options') or []
    if len(options) >= 2 and item.get('item_type') == 'multiple_choice':
        vocab = _vocab_translations(p, options)
        if vocab:
            return vocab

    return ''


_VOCAB_HINTS: dict[str, dict[str, str]] = {
    'кофе': {'coffee': 'кофе ✅', 'tea': 'чай', 'water': 'вода'},
    'книга': {'book': 'книга ✅', 'door': 'дверь', 'bag': 'сумка'},
    'библиотека': {'library': 'библиотека ✅', 'hospital': 'больница', 'station': 'станция'},
    'corroborate': {
        'corroborate': 'подтверждать ✅',
        'confuse': 'путать',
        'consist': 'состоять (consist of)',
        'complain': 'жаловаться',
    },
    'responsibility': {
        'took': 'взял(а) ✅ (take responsibility)',
        'made': 'сделал(а) — не collocate',
        'did': 'сделал(а) — не collocate',
        'got': 'получил(а) — другое значение',
    },
}


def _vocab_translations(prompt: str, options: list[str]) -> str:
    prompt_l = prompt.lower()
    for key, mapping in _VOCAB_HINTS.items():
        if key in prompt_l or any(key in (o or '').lower() for o in options):
            lines = ['<b>Значения вариантов:</b>']
            for opt in options:
                hint = mapping.get(opt.lower()) or mapping.get(opt)
                if hint:
                    lines.append(f'• <b>{opt}</b> — {hint}')
            return '\n'.join(lines) if len(lines) > 1 else ''
    return ''
