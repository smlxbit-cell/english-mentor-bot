"""Merge RU + EN speech-to-text for mixed tutor messages."""

from __future__ import annotations

import re

from ai_app.services.grammar import is_garbage_transcript

# Latin spellings of common Russian words (bad EN-model output on Russian speech).
_RU_PHONETIC_LATIN = frozenset({
    'ya', 'ty', 'vy', 'on', 'ona', 'eto', 'chto', 'kak', 'kto', 'gde', 'pochemu',
    'vopros', 'otvet', 'na', 'po', 'russkom', 'russki', 'russkiy', 'govori',
    'govorit', 'govorite', 'govorii', 'pogovorii', 'pogovori', 'mozhesh', 'mozhno',
    'hocu', 'hochu', 'privet', 'zdravstvuyte', 'pozhaluysta', 'spasibo', 'mne',
    'tebe', 'menya', 'tebya', 'mena', 'est', 'somnenia', 'somneniya', 'mesto', 'mesters',
    'jakie', 'kakie', 'temy', 'temi', 'mozesz', 'mozesh', 'moj', 'moya', 'pogovorid',
    'pogovorit', 'pogovory', 'zamyszysz', 'zamyslit',
    's', 'so', 'mnoj', 'mnoy', 'mnoi', 'toboj', 'esli',
    'kogda', 'segodnya', 'segodne', 'horosho', 'ploho', 'davaj', 'davay', 'skazhi',
    'skazhite', 'raskaji', 'raskazhi', 'pogovorit', 'pogovorim', 'anglijski',
    'angliyski', 'angliyskom',     'atvet', 'wopros', 'vot', 'razvehvati', 'razvivat', 'razvivati', 'ragbiet',
    'prodvigat', 'prodvigati', 'anglijski', 'angliyski', 'kanal',
})

# Polish / other Slavic STT noise when the EN model hears Russian speech.
_SLAVIC_STT_JUNK = frozenset({
    'czy', 'czym', 'jak', 'jakie', 'jakis', 'poniesiesz', 'rozumiesz', 'rozumie',
    'mowisz', 'mowimy', 'powiedz', 'ruski', 'ruska', 'ruskiej', 'ruskowicz',
    'ruskowic', 'russk', 'po', 'polsku', 'jezyk', 'jezyku',
})

_COMMON_EN = frozenset({
    'a', 'an', 'the', 'i', 'you', 'we', 'they', 'he', 'she', 'it', 'am', 'is',
    'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
    'can', 'could', 'will', 'would', 'what', 'how', 'why', 'when', 'where', 'who',
    'today', 'feel', 'feeling', 'feelings', 'talk', 'speak', 'english', 'please',
    'hello', 'hi', 'yes', 'no', 'not', 'with', 'about', 'your', 'my', 'me',
    'fallen', 'fall', 'wrong', 'correct', 'answer', 'question', 'll',
})

_FILLER_EN = frozenset({
    'a', 'an', 'the', 'i', 'am', 'is', 'are', 'was', 'were', 'be', 'uh', 'um', 'oh', 'eh',
    'mm', 'hm', 'hmm', 'er', 'ah',
})

# English words mis-heard into Cyrillic by the RU STT model.
_CYR_PHONETIC_EN_MAP = {
    'ай': 'I', 'айл': "I'll", 'айм': "I'm", 'аил': "I'll",
    'фил': 'feel', 'филин': 'feel', 'филинг': 'feeling',
    'тудей': 'today', 'тудэй': 'today',
    'хау': 'how', 'хоу': 'how', 'ду': 'do', 'дью': 'do', 'ю': 'you',
    'ми': 'me', 'май': 'my', 'йор': 'your', 'ёр': 'your',
    'вот': 'what', 'толк': 'talk', 'спик': 'speak', 'спикинг': 'speaking',
    'инглиш': 'English', 'инглишчан': 'English channel', 'инглишчэн': 'English channel',
    'инглишченел': 'English channel', 'ченнел': 'channel', 'чэнел': 'channel',
    'энд': 'and', 'виз': 'with', 'эбаут': 'about',
    'плиз': 'please', 'хэв': 'have', 'хас': 'has', 'фолен': 'fallen',
    'энсвер': 'answer', 'квешен': 'question',
    'гуэйт': 'great', 'грейт': 'great', 'грит': 'great', 'греат': 'great',
    'гуд': 'good', 'бэд': 'bad', 'файн': 'fine', 'окей': 'okay', 'ок': 'okay',
    'йес': 'yes', 'ноу': 'no', 'сори': 'sorry', 'хелло': 'hello', 'хеллоу': 'hello',
    'райт': 'right', 'вронг': 'wrong', 'вэл': 'well', 'сэй': 'say', 'сай': 'say',
    'вэйт': 'wait', 'лэйт': 'late', 'тэнкс': 'thanks', 'сэнкс': 'thanks',
}

_PHONETIC_EN_SUFFIXES = ('тудей', 'тудэй', 'инг', 'айл', 'айм', 'линг', 'ейт', 'эйт', 'ейшн', 'лиш')

# Hints that RU and EN transcripts are the same phrase (EN speech → RU mishear).
_RU_EN_PARALLEL_HINTS = (
    ('сегодня', 'today'),
    ('поговор', 'talk'),
    ('говор', 'speak'),
    ('мной', 'me'),
    ('мне', 'me'),
    ('можешь', 'can'),
    ('можно', 'can'),
    ('ты', 'you'),
    ('теб', 'you'),
    ('как', 'how'),
    ('что', 'what'),
    ('где', 'where'),
    ('чувств', 'feel'),
    ('ответ', 'answer'),
    ('вопрос', 'question'),
    ('привет', 'hello'),
    ('здрав', 'hello'),
    ('путешеств', 'travel'),
    ('люблю', 'love'),
    ('люб', 'like'),
    ('собак', 'dog'),
    ('книг', 'book'),
    ('канал', 'channel'),
    ('развива', 'develop'),
    ('продвига', 'promote'),
    ('объясн', 'explain'),
    ('граммат', 'grammar'),
    ('предлож', 'sentence'),
)

# EN-model phonetic spelling of Russian words the learner said when they forgot English.
_PHONETIC_RU_LATIN_HINTS: dict[str, str] = {
    'razvehvati': 'развивать',
    'razvivat': 'развивать',
    'razvivati': 'развивать',
    'ragbiet': 'продвигать',
    'prodvigat': 'продвигать',
    'prodvigati': 'продвигать',
    'razvit': 'развить',
    'prodvit': 'продвинуть',
    'redhav': 'развивать',
    'readhav': 'развивать',
    'improv': 'улучшать',
    'impruve': 'улучшать',
    'improove': 'улучшать',
    'uluchshat': 'улучшать',
    'uluchshit': 'улучшить',
    'mesters': 'место',
    'mester': 'место',
    'mesto': 'место',
    'mest': 'место',
    'deistvitelno': 'действительно',
    'deystvitelno': 'действительно',
    'nahoditsya': 'находиться',
    'nahoditsa': 'находиться',
    'khotu': 'хотеть',
    'hochu': 'хотеть',
    'hocu': 'хотеть',
    'byt': 'быть',
    'bit': 'быть',
    'knigi': 'книги',
    'kniga': 'книга',
    'knig': 'книги',
    'citat': 'читать',
    'chitat': 'читать',
    'chit': 'читать',
    'shestertva': 'путешествовать',
    'puteshestvovat': 'путешествовать',
    'puteshestv': 'путешествовать',
    'puta': 'путешествовать',
    'kniggee': 'книги',
    'knigge': 'книги',
    'knigy': 'книги',
}

# Prefixes that map fuzzy EN-STT spellings of Russian words → Cyrillic.
_PHONETIC_RU_PREFIXES: tuple[tuple[str, str], ...] = (
    ('knig', 'книги'),
    ('chit', 'читать'),
    ('cit', 'читать'),
    ('putesh', 'путешествовать'),
    ('shesterv', 'путешествовать'),
)

# Plausible verbs between «I want to … my English channel/pronunciation».
_VALID_CHANNEL_VERBS = frozenset({
    'develop', 'grow', 'promote', 'improve', 'build', 'run', 'start', 'expand', 'create',
})

_VALID_GOAL_VERBS = _VALID_CHANNEL_VERBS | frozenset({
    'practice', 'learn', 'study', 'enhance', 'boost', 'polish', 'fix', 'master', 'work',
    'travel', 'read', 'write', 'speak', 'listen',
})

_STT_NOUN_GARBAGE = frozenset({
    'mesters', 'mester', 'mesto', 'mest', 'masters', 'master',
})

# Whisper often mishears «improve» / Russian «улучшать» as these.
_STT_VERB_GARBAGE = frozenset({
    'launch', 'launches', 'launched', 'lounge', 'lounges', 'lunch', 'lunches',
    'lanuch', 'lanch', 'read', 'have', 'it', 'improv', 'impruve', 'improove',
    'readhave', 'redhav', 'razvehvati', 'razvivat',
})

_STT_VERB_GARBAGE_PHRASES = frozenset({
    'launch it', 'lounge it', 'lunch it', 'read have', 'red have', 'readhave',
})

_STT_VERB_HOMOPHONE_FIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r'\b(i want to)\s+launch\s+it\b', re.I), r'\1 …'),
    (re.compile(r'\b(i want to)\s+lounge\s+it\b', re.I), r'\1 …'),
    (re.compile(r'\b(i want to)\s+lunch\s+it\b', re.I), r'\1 …'),
    (re.compile(r'\b(i want to)\s+launch\b', re.I), r'\1 …'),
    (re.compile(r'\b(i want to)\s+lounge\b', re.I), r'\1 …'),
    (re.compile(r'\b(i want to)\s+lunch\b', re.I), r'\1 …'),
)

_TRAILING_QUESTION_RE = re.compile(
    r'\s+((?:what|how|where|why|when|who)\s+should\s+(?:i|we)\b.+)$',
    re.I,
)

_STT_WORD_SALAD_RE = re.compile(
    r'\b(thompson|tompson|sompson|samson|thomson)\b.*\b(woman|women|man)\b'
    r'|\b(read have|red have|readhav)\b'
    r'|\b(launch it|lounge it|lunch it)\b',
    re.I,
)

_RU_SKIP_IN_FORGOTTEN = frozenset({
    'я', 'ты', 'он', 'она', 'мы', 'вы', 'они', 'и', 'в', 'на', 'с', 'со', 'к', 'ко',
    'мой', 'моя', 'моё', 'мои', 'свой', 'своя', 'свои', 'хочу', 'хотел', 'хотела',
    'как', 'что', 'это', 'вот', 'ну', 'а', 'но', 'ли', 'бы', 'же', 'тоже', 'ещё',
    'еще', 'очень', 'сегодня', 'английский', 'английская', 'канал', 'channel',
})

# Real Russian words — if RU pass has none of these, it is likely English mis-heard as Cyrillic.
_RU_REAL_SPEECH_MARKERS = frozenset({
    'я', 'ты', 'вы', 'он', 'она', 'оно', 'мы', 'они', 'мне', 'тебе', 'меня', 'тебя',
    'мой', 'моя', 'мои', 'твой', 'твоя', 'наш', 'ваш', 'свой', 'своя',
    'и', 'в', 'на', 'с', 'со', 'по', 'к', 'у', 'о', 'не', 'да', 'нет', 'ну', 'а', 'но',
    'что', 'как', 'где', 'когда', 'почему', 'кто', 'это', 'вот', 'тут', 'там', 'здесь',
    'хочу', 'хотел', 'хотела', 'могу', 'можно', 'нужно', 'есть', 'был', 'была', 'буду',
    'говорить', 'говорю', 'сказать', 'скажи', 'знать', 'знаю', 'понять', 'понимаю',
    'делать', 'быть', 'иметь', 'думать', 'помочь', 'помоги', 'расскажи', 'поговорим',
    'место', 'слово', 'слова', 'вопрос', 'вопросы', 'ответ', 'английский', 'русский',
    'сегодня', 'очень', 'хорошо', 'плохо', 'пожалуйста', 'спасибо', 'привет',
    'действительно', 'развивать', 'улучшать', 'продвигать', 'практиковать', 'учить',
    'забыл', 'забыла', 'забыть', 'правильно', 'неправильно', 'ошибка', 'грамматика',
    'произношение', 'диалог', 'разговор', 'предложение', 'фраза', 'значит',
    'какие', 'какой', 'какая', 'темы', 'тема', 'ты', 'можешь', 'мной', 'со', 'поговорить',
    'поговорим', 'расскажи', 'рассказать', 'интересно', 'хотел', 'хотела', 'спросить',
})

def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r'[А-Яа-яЁё]', text or ''))


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r'\s+', (text or '').strip()) if t]


def _bare_word(token: str) -> str:
    return re.sub(r'^[^\w\d]+|[^\w\d]+$', '', token.lower())


def is_cyrillic_phonetic_english(word: str) -> bool:
    w = _bare_word(word)
    if not w:
        return False
    if w in _CYR_PHONETIC_EN_MAP:
        return True
    if not re.fullmatch(r'[а-яё]+', w):
        return False
    if w.startswith('инглиш') and len(w) >= 6:
        return True
    if any(w.endswith(s) for s in _PHONETIC_EN_SUFFIXES):
        return True
    return w in {'ай', 'хау', 'ду', 'ю', 'ми', 'лл', 'ок'}


def _english_phrase_from_cyrillic(word: str) -> str:
    """Best-effort English phrase for a Cyrillic phonetic token."""
    w = _bare_word(word)
    if not w:
        return ''
    if w in _CYR_PHONETIC_EN_MAP:
        return _CYR_PHONETIC_EN_MAP[w].lower()
    if w.startswith('инглиш'):
        return 'english channel'
    mapped = decyrillify_english_phonetic(w).lower()
    return mapped if mapped != w else ''


def _forgotten_word_already_in_english(word: str, en_context: str) -> bool:
    """Skip «забыл слова» when Whisper already captured the English."""
    en_low = (en_context or '').lower()
    if not en_low:
        return False
    phrase = _english_phrase_from_cyrillic(word)
    if phrase and phrase in en_low:
        return True
    if phrase:
        parts = [p for p in phrase.split() if len(p) >= 3]
        if parts and all(p in en_low for p in parts):
            return True
    return False


def _resolve_phonetic_ru_latin(word: str) -> str:
    """Map EN-model phonetic spelling of a Russian word to Cyrillic."""
    bare = _bare_word(word).lower()
    if not bare:
        return word
    if bare in _PHONETIC_RU_LATIN_HINTS:
        return _PHONETIC_RU_LATIN_HINTS[bare]
    for prefix, cyrillic in _PHONETIC_RU_PREFIXES:
        if bare.startswith(prefix):
            return cyrillic
    if looks_like_phonetic_russian_latin(bare):
        return bare
    return word


def _split_english_phonetic_tail(words: list[str]) -> tuple[list[str], list[str]]:
    """Split STT tail into kept English words vs forgotten Russian (Cyrillic)."""
    english: list[str] = []
    forgotten: list[str] = []
    for raw in words:
        bare = _bare_word(raw)
        if not bare or (len(bare) == 1 and bare in {'t', 'a', 'i'}):
            continue
        resolved = _resolve_phonetic_ru_latin(bare)
        is_phonetic = (
            resolved != bare
            or bare in _PHONETIC_RU_LATIN_HINTS
            or looks_like_phonetic_russian_latin(bare)
        )
        if is_phonetic:
            cyr = resolved if _has_cyrillic(resolved) else _PHONETIC_RU_LATIN_HINTS.get(bare, resolved)
            if cyr and cyr not in forgotten:
                forgotten.append(cyr)
        else:
            english.append(raw)
    return english, forgotten


def _filter_forgotten_words(forgotten: list[str], en_context: str) -> list[str]:
    out: list[str] = []
    for w in forgotten:
        if _forgotten_word_already_in_english(w, en_context):
            continue
        if w not in out:
            out.append(w)
    return out


def decyrillify_english_phonetic(text: str) -> str:
    words = [_bare_word(w) for w in _tokenize(text)]
    out: list[str] = []
    for w in words:
        if not w:
            continue
        out.append(_CYR_PHONETIC_EN_MAP.get(w, w))
    return ' '.join(out)


def _format_english_display(text: str) -> str:
    text = normalize_english_fragment(text)
    if not text:
        return ''
    words = text.split()
    if len(words) == 1:
        return words[0].capitalize()
    return text


def phonetic_english_only_line(text: str) -> str:
    """Cyrillic line that is only English words in phonetic spelling (e.g. «Гуэйт»)."""
    if not text or not _has_cyrillic(text):
        return ''
    tokens = _tokenize(text)
    if not tokens or len(tokens) > 5:
        return ''
    if not all(is_cyrillic_phonetic_english(t) for t in tokens):
        return ''
    converted = decyrillify_english_phonetic(text)
    if not converted or not is_meaningful_english_fragment(converted):
        return ''
    return _format_english_display(converted)


def normalize_english_fragment(text: str) -> str:
    if not text:
        return ''
    out = text.strip()
    out = re.sub(r'\bi\s+ll\b', "I'll", out, flags=re.I)
    out = re.sub(r'\bi\s+m\b', "I'm", out, flags=re.I)
    out = re.sub(r'\bim\b', "I'm", out, flags=re.I)
    out = re.sub(r'\byou\s+re\b', "you're", out, flags=re.I)
    out = re.sub(r'\bthey\s+re\b', "they're", out, flags=re.I)
    out = re.sub(r'\bwe\s+re\b', "we're", out, flags=re.I)
    out = re.sub(r'\bhe\s+s\b', "he's", out, flags=re.I)
    out = re.sub(r'\bshe\s+s\b', "she's", out, flags=re.I)
    out = re.sub(r'\bit\s+s\b', "it's", out, flags=re.I)
    out = re.sub(r'\bfillin\b', 'feeling', out, flags=re.I)
    out = re.sub(r'\bfilin\b', 'feel', out, flags=re.I)
    out = re.sub(r'\btutey\b', 'today', out, flags=re.I)
    for pattern, repl in (
        (r"\bdon\s+t\b", "don't"),
        (r"\bwon\s+t\b", "won't"),
        (r"\bcan\s+t\b", "can't"),
        (r"\bdoesn\s+t\b", "doesn't"),
        (r"\bdidn\s+t\b", "didn't"),
        (r"\bisn\s+t\b", "isn't"),
        (r"\baren\s+t\b", "aren't"),
        (r"\bwasn\s+t\b", "wasn't"),
        (r"\bweren\s+t\b", "weren't"),
        (r"\bhaven\s+t\b", "haven't"),
        (r"\bhasn\s+t\b", "hasn't"),
        (r"\bhadn\s+t\b", "hadn't"),
        (r"\bwouldn\s+t\b", "wouldn't"),
        (r"\bcouldn\s+t\b", "couldn't"),
        (r"\bshouldn\s+t\b", "shouldn't"),
    ):
        out = re.sub(pattern, repl, out, flags=re.I)
    out = re.sub(r'\s+', ' ', out).strip()
    return out


# Words STT often lowercases — not learner mistakes when input was voice.
_VOICE_ALWAYS_CAP = {
    'i': 'I',
    'english': 'English',
    'russian': 'Russian',
    'american': 'American',
    'british': 'British',
    'london': 'London',
    'telegram': 'Telegram',
}


def _collapse_adjacent_word_repeats(text: str, *, max_word_len: int = 14) -> str:
    """Thinking pauses / STT echo: «my my dog» → «my dog», «I I want» → «I want»."""
    words = text.split()
    if len(words) < 2:
        return text
    out: list[str] = []
    i = 0
    while i < len(words):
        raw = words[i]
        bare = _bare_word(raw)
        if bare and len(bare) <= max_word_len:
            j = i + 1
            while j < len(words) and _bare_word(words[j]) == bare:
                j += 1
            if j > i + 1:
                out.append(raw)
                i = j
                continue
        out.append(raw)
        i += 1
    return ' '.join(out)


def _dedupe_stt_stutter(text: str) -> str:
    """Remove immediate phrase repetition from STT (e.g. «I would like i would like…»)."""
    text = _collapse_adjacent_word_repeats(text)
    words = text.split()
    if len(words) < 4:
        return text
    for size in range(min(len(words) // 2, 10), 2, -1):
        for start in range(len(words) - 2 * size + 1):
            a = [w.lower() for w in words[start:start + size]]
            b = [w.lower() for w in words[start + size:start + 2 * size]]
            if a == b:
                return ' '.join(words[: start + size] + words[start + 2 * size :])
    return text


def _capitalize_voice_english(text: str) -> str:
    words = text.split()
    if not words:
        return text
    out: list[str] = []
    sentence_start = True
    for raw in words:
        bare = re.sub(r"[^\w']", '', raw)
        low = bare.lower()
        if low in _VOICE_ALWAYS_CAP:
            fixed = _VOICE_ALWAYS_CAP[low]
            if bare:
                new = re.sub(re.escape(bare), fixed, raw, count=1, flags=re.I)
            else:
                new = fixed
            sentence_start = False
        elif sentence_start and bare:
            new = raw[:1].upper() + raw[1:] if len(raw) > 1 else raw.upper()
            sentence_start = False
        else:
            new = raw
        if raw.endswith(('.', '!', '?')):
            sentence_start = True
        out.append(new)
    return ' '.join(out)


def _fix_stt_verb_homophones(text: str) -> str:
    out = text or ''
    for pattern, repl in _STT_VERB_HOMOPHONE_FIXES:
        out = pattern.sub(repl, out)
    return out


def _fix_voice_word_forms(text: str) -> str:
    """Common spoken slips — fix before tutor, not as errors."""
    fixes = (
        (re.compile(r'\benglish pronouncing\b', re.I), 'English pronunciation'),
        (re.compile(r'\bmy english pronouncing\b', re.I), 'my English pronunciation'),
        (re.compile(r'\bmy pronouncing\b', re.I), 'my pronunciation'),
    )
    out = text
    for pattern, repl in fixes:
        out = pattern.sub(repl, out)
    return out


def normalize_voice_english_transcript(text: str) -> str:
    """Clean STT artifacts before showing or grading spoken English."""
    text = normalize_english_fragment((text or '').strip())
    if not text:
        return ''
    text = _fix_stt_verb_homophones(text)
    text = _fix_voice_word_forms(text)
    text = _dedupe_stt_stutter(text)
    text = _capitalize_voice_english(text)
    return text.strip()


def looks_like_stt_word_salad(text: str) -> bool:
    """Obvious STT mishearing (e.g. «something wrong» → «thompson a woman»)."""
    low = (text or '').strip().lower()
    if not low:
        return False
    if _STT_WORD_SALAD_RE.search(low):
        return True
    if re.search(r'\bif i said\b', low):
        tail = re.split(r'\bif i said\b', low, maxsplit=1, flags=re.I)[-1].strip()
        if tail and not _is_plausible_if_i_said_tail(tail):
            return True
    return False


def _is_plausible_if_i_said_tail(tail: str) -> bool:
    low = tail.strip().lower().rstrip('.')
    if re.search(r'\b(something|anything|nothing)\s+wrong\b', low):
        return True
    if re.search(r'\b(a mistake|incorrect|incorrectly|wrong)\b', low):
        return True
    if re.search(r'\bwrong\b', low):
        return True
    if len(low.split()) <= 2 and not _STT_WORD_SALAD_RE.search(low):
        return True
    return False


def sanitize_stt_garbage_clauses(text: str) -> str:
    """Replace obvious misheard tails with a gap before showing or grading."""
    text = (text or '').strip()
    if not text:
        return ''
    m = re.search(r'(.+?\bif i said)\s+(.+)$', text, re.I)
    if m:
        tail = m.group(2).strip().rstrip('.')
        if looks_like_stt_word_salad(tail) or not _is_plausible_if_i_said_tail(tail):
            text = f'{m.group(1).strip()} …'
    return text


def _english_frame_needs_russian_words(en: str) -> bool:
    """English lead-in that trails off — learner continued in Russian."""
    en = (en or '').strip().rstrip('.')
    if not en:
        return False
    low = en.lower()
    if re.search(r'\bi have (?:some )?questions about$', low):
        return True
    if re.search(r'\bhow (?:do you|to) say$', low):
        return True
    if re.search(r'\bwhat (?:is|does)\b', low) and low.endswith('mean'):
        return True
    for tail in ('about', 'for', 'on', 'to', 'mean'):
        if low.endswith(f' {tail}') or low.endswith(tail):
            if is_meaningful_english_fragment(en):
                return True
    return False


def _scaffold_english_lead_in(en: str) -> str:
    en = normalize_voice_english_transcript((en or '').strip())
    if not en:
        return ''
    if '…' in en:
        return en
    return f'{en.rstrip(".")} …'


def scaffold_i_have_questions_about(en: str) -> str:
    """I have some questions about Mesters … → scaffold with gap."""
    en = collapse_voice_fillers((en or '').strip())
    prefix, question = split_trailing_english_question(en)
    m = re.match(r'^(i have (?:some )?questions about)\s+(.+)$', prefix.strip(), re.I)
    if not m:
        return ''
    lead = m.group(1)
    raw_tail = m.group(2).strip()
    if not raw_tail:
        return ''
    needs_gap = (
        looks_like_transliterated_russian(raw_tail)
        or any(_bare_word(w) in _STT_NOUN_GARBAGE for w in raw_tail.split())
        or any(looks_like_phonetic_russian_latin(_bare_word(w)) for w in raw_tail.split())
    )
    if not needs_gap and is_meaningful_english_fragment(f'{lead} {raw_tail}'):
        return ''
    scaffold = normalize_voice_english_transcript(f'{lead} …')
    result = scaffold
    if question:
        result += f'\n{normalize_voice_english_transcript(question)}'
    return result


def _repair_whisper_en_plus_phonetic_ru(text: str) -> str:
    """One Whisper line: English start + phonetic Russian tail (no Cyrillic)."""
    text = collapse_voice_fillers((text or '').strip())
    if not text or _has_cyrillic(text):
        return ''
    scaffolded = scaffold_i_have_questions_about(text)
    if scaffolded:
        return scaffolded
    m = re.match(
        r'^((?:i want to|how do you say|what is)\b.+?)(\s+.+)$',
        text,
        re.I,
    )
    if not m:
        return ''
    lead, tail = m.group(1).strip(), m.group(2).strip()
    if not _english_frame_needs_russian_words(lead) and not looks_like_transliterated_russian(tail):
        return ''
    forgotten: list[str] = []
    for w in tail.split():
        bare = _bare_word(w)
        if not bare or bare in _COMMON_EN or bare in _STT_NOUN_GARBAGE:
            continue
        hint = _PHONETIC_RU_LATIN_HINTS.get(bare)
        if hint:
            if hint not in forgotten:
                forgotten.append(hint)
    scaffold = _scaffold_english_lead_in(lead)
    if not scaffold:
        return ''
    if forgotten:
        return f'{scaffold}\n(забыл слова: {", ".join(forgotten[:4])})'
    return scaffold


def split_whisper_mixed(text: str) -> tuple[str, str]:
    """Split one Whisper line that mixes Cyrillic and Latin into RU + EN parts."""
    text = (text or '').strip()
    if not text or not _has_cyrillic(text):
        return '', text
    if not re.search(r'[A-Za-z]', text):
        return text, ''
    ru_tokens: list[str] = []
    en_tokens: list[str] = []
    for raw in text.split():
        if _has_cyrillic(raw):
            ru_tokens.append(raw)
        elif re.search(r"[A-Za-z]", raw):
            en_tokens.append(raw)
    return ' '.join(ru_tokens).strip(), ' '.join(en_tokens).strip()


def merge_whisper_tutor_transcript(text: str) -> str:
    """Normalize a single Whisper transcript for the tutor pipeline."""
    text = collapse_voice_fillers((text or '').strip())
    if not text:
        return ''
    ru, en = split_whisper_mixed(text)
    if ru and en:
        merged = merge_tutor_transcripts(ru, en)
        return merged or scaffold_i_want_to_english_goal(text)
    if ru:
        return ru
    cleaned = sanitize_stt_garbage_clauses(text)
    scaffolded = scaffold_i_have_questions_about(cleaned) or scaffold_i_want_to_english_goal(cleaned)
    if scaffolded and '…' in scaffolded:
        return prepare_tutor_voice_transcript(scaffolded)
    repaired = _repair_whisper_en_plus_phonetic_ru(text)
    if repaired:
        return repaired
    return prepare_tutor_voice_transcript(cleaned)


def collapse_voice_fillers(text: str) -> str:
    """Remove long um/м/э hesitations from STT."""
    if not text:
        return ''
    out = text
    out = re.sub(r'[umhаэy]{8,}', ' ', out, flags=re.I)
    out = re.sub(r'\b[umh]{4,}\b', ' ', out, flags=re.I)
    out = re.sub(r'\s+', ' ', out).strip()
    return out


def looks_like_phonetic_russian_latin(word: str) -> bool:
    w = _bare_word(word)
    if not w or _has_cyrillic(w):
        return False
    if w in _PHONETIC_RU_LATIN_HINTS or w in _RU_PHONETIC_LATIN:
        return True
    if len(w) >= 6 and re.search(r'(vati|viet|giet|zhiv|prodv|razv|ragbi|readhav|redhav|knig|chit|citat|putesh|shesterv)', w):
        return True
    return False


def split_trailing_english_question(en: str) -> tuple[str, str]:
    """Split a valid trailing wh-question from STT noise before it."""
    m = _TRAILING_QUESTION_RE.search(en or '')
    if m:
        return en[:m.start()].strip(), m.group(1).strip()
    return (en or '').strip(), ''


def _looks_like_stt_garbage_verb(middle: str) -> bool:
    low = (middle or '').strip().lower()
    if not low:
        return True
    if low in _STT_VERB_GARBAGE_PHRASES:
        return True
    tokens = [_bare_word(t) for t in low.split()]
    tokens = [t for t in tokens if t]
    if not tokens:
        return True
    if len(tokens) == 1 and tokens[0] in _STT_VERB_GARBAGE:
        return True
    if len(tokens) == 2 and f'{tokens[0]} {tokens[1]}' in _STT_VERB_GARBAGE_PHRASES:
        return True
    if any(looks_like_phonetic_russian_latin(t) for t in tokens):
        return True
    return False


def _is_plausible_goal_verb_phrase(middle: str) -> bool:
    tokens = [_bare_word(t) for t in middle.split()]
    tokens = [t for t in tokens if t]
    if not tokens:
        return False
    if len(tokens) == 1:
        return tokens[0] in _VALID_GOAL_VERBS
    if len(tokens) == 3 and tokens[1] == 'and':
        return tokens[0] in _VALID_GOAL_VERBS and tokens[2] in _VALID_GOAL_VERBS
    if len(tokens) == 2 and tokens[0] == 'work' and tokens[1] == 'on':
        return True
    return False


def _guess_forgotten_for_english_goal(goal: str) -> list[str]:
    g = (goal or '').lower()
    if g == 'pronunciation':
        return ['улучшать']
    if g == 'channel':
        return ['развивать']
    return []


def scaffold_i_like_to(en: str) -> str:
    """I like/love to [English + optional Russian phonetics] → frame + forgotten words."""
    en = _fix_stt_verb_homophones((en or '').strip())
    prefix, question = split_trailing_english_question(en)
    m = re.match(r'^(i (?:like|love) to)\s+(.+)$', prefix.strip(), re.I)
    if not m:
        return ''
    lead = m.group(1)
    tail = m.group(2).strip()
    eng_words, forgotten = _split_english_phonetic_tail(tail.split())
    eng_tail = ' '.join(eng_words).strip()

    if eng_tail and not forgotten:
        return normalize_voice_english_transcript(f'{lead} {eng_tail}')

    if eng_tail and forgotten:
        frame = normalize_voice_english_transcript(f'{lead} {eng_tail}')
        result = f'{frame}\n(забыл слова: {", ".join(forgotten)})'
        if question:
            result += f'\n{normalize_voice_english_transcript(question)}'
        return result

    if forgotten or _looks_like_stt_garbage_verb(tail):
        forgotten = forgotten or [
            _resolve_phonetic_ru_latin(w)
            for w in tail.split()
            if looks_like_phonetic_russian_latin(_bare_word(w))
            or _bare_word(w) in _PHONETIC_RU_LATIN_HINTS
        ]
        seen: set[str] = set()
        unique: list[str] = []
        for word in forgotten:
            cyr = word if _has_cyrillic(word) else _PHONETIC_RU_LATIN_HINTS.get(_bare_word(word), word)
            if cyr not in seen:
                seen.add(cyr)
                unique.append(cyr)
        scaffold = normalize_voice_english_transcript(f'{lead} …')
        result = (
            f'{scaffold}\n(забыл слова: {", ".join(unique)})'
            if unique else scaffold
        )
        if question:
            result += f'\n{normalize_voice_english_transcript(question)}'
        return result
    return ''


def scaffold_i_want_to_english_goal(en: str) -> str:
    """I want to launch/lounge … my English pronunciation → scaffold + forgotten hint."""
    en = _fix_stt_verb_homophones((en or '').strip())
    prefix, question = split_trailing_english_question(en)
    m_gap = re.match(
        r'^(i want to)\s+((?:my\s+)?english\s+(channel|pronunciation|speaking))\s*$',
        prefix.strip(),
        re.I,
    )
    if m_gap:
        scaffold = normalize_voice_english_transcript(f'{m_gap.group(1)} … {m_gap.group(2)}')
        forgotten = _guess_forgotten_for_english_goal(
            re.search(r'english\s+(\w+)', m_gap.group(2), re.I).group(1),
        )
        result = (
            f'{scaffold}\n(забыл слова: {", ".join(forgotten)})'
            if forgotten else scaffold
        )
        if question:
            result += f'\n{normalize_voice_english_transcript(question)}'
        return result
    m = re.match(
        r'^(i want to)\s+(.+?)\s+((?:my\s+)?english\s+(channel|pronunciation|speaking))\s*$',
        prefix.strip(),
        re.I,
    )
    if not m:
        return normalize_voice_english_transcript(en)
    middle = m.group(2).strip()
    goal_tail = m.group(3)
    goal = m.group(4)
    if _is_plausible_goal_verb_phrase(middle):
        result = normalize_voice_english_transcript(prefix)
    elif _looks_like_stt_garbage_verb(middle):
        scaffold = normalize_voice_english_transcript(f'{m.group(1)} … {goal_tail}')
        forgotten = _guess_forgotten_for_english_goal(goal)
        result = (
            f'{scaffold}\n(забыл слова: {", ".join(forgotten)})'
            if forgotten else scaffold
        )
    else:
        result = normalize_voice_english_transcript(prefix)
    if question:
        result += f'\n{normalize_voice_english_transcript(question)}'
    return result


def _is_plausible_channel_verb_phrase(middle: str) -> bool:
    return _is_plausible_goal_verb_phrase(middle)


def _scaffold_i_want_to_channel(prefix: str) -> str:
    """I want to read have my English channel → I want to … my English channel."""
    return scaffold_i_want_to_english_goal(prefix)


def _extract_ru_forgotten_words(ru: str) -> list[str]:
    if not _has_cyrillic(ru):
        return []
    words = re.findall(r'[А-Яа-яЁё]+', ru)
    out: list[str] = []
    for w in words:
        low = w.lower()
        if low in _RU_SKIP_IN_FORGOTTEN or len(low) < 4:
            continue
        if is_cyrillic_phonetic_english(w):
            continue
        if w not in out:
            out.append(w)
    return out[:4]


def _english_scaffold_from_en(en: str) -> str:
    en = collapse_voice_fillers(en)
    parts: list[str] = []
    for raw in en.split():
        bare = _bare_word(raw)
        if not bare or re.fullmatch(r'[umh]{2,}', bare, re.I):
            continue
        if looks_like_phonetic_russian_latin(bare):
            if parts and parts[-1] != '…':
                parts.append('…')
            continue
        parts.append(raw)
    text = ' '.join(parts)
    text = re.sub(r'(…\s*)+', '… ', text).strip()
    text = re.sub(r'\s+…', ' …', text)
    return normalize_voice_english_transcript(text)


def lacks_english_content(en: str) -> bool:
    """True when a Latin STT line has almost no real English words (RU mis-heard as EN)."""
    words = re.findall(r"[a-z']+", (en or '').lower())
    if not words:
        return True
    signal = sum(
        1 for w in words
        if w in _COMMON_EN or (len(w) >= 4 and not looks_like_phonetic_russian_latin(w))
    )
    return signal < 2


def _clean_russian_utterance(ru: str) -> bool:
    """Cyrillic speech without embedded phonetic-English junk in the RU pass."""
    if not ru or not _has_cyrillic(ru):
        return False
    words = re.findall(r'[а-яё]+', ru.lower())
    if len(words) < 3:
        return False
    phonetic = sum(1 for w in words if is_cyrillic_phonetic_english(w))
    return phonetic == 0 and not re.search(r'[a-z]', ru.lower())


def _has_slavic_stt_junk_en_pass(en: str) -> bool:
    words = re.findall(r"[a-z']+", (en or '').lower())
    return any(w in _SLAVIC_STT_JUNK for w in words)


def _en_pass_has_real_english_frame(en: str) -> bool:
    """True when the EN STT line is clearly English-primary, not Slavic junk."""
    if not en or _has_slavic_stt_junk_en_pass(en):
        return False
    low = en.lower()
    return bool(re.search(
        r'\b(i want to|i would like|i like to|i love to|i have\b|can you|could you)\b',
        low,
    ))


def _both_passes_same_english(ru: str, en: str) -> bool:
    """Both STT passes returned the same Latin text (common when RU audio hits EN model)."""
    ru = normalize_english_fragment((ru or '').strip())
    en = normalize_english_fragment((en or '').strip())
    if not ru or not en or _has_cyrillic(ru) or _has_cyrillic(en):
        return False
    low_ru, low_en = ru.lower(), en.lower()
    return low_ru == low_en or low_ru in low_en or low_en in low_ru


def _prefer_russian_over_en_translation(ru: str, en: str) -> bool:
    """Fluent Cyrillic RU + Latin EN that looks like auto-translation, not learner speech."""
    ru = (ru or '').strip()
    en = (en or '').strip()
    if not _clean_russian_utterance(ru) or not _ru_has_real_russian_markers(ru):
        return False
    if not en or _has_cyrillic(en):
        return False
    ru_word_count = len(re.findall(r'[а-яё]+', ru.lower()))
    if ru_word_count < 6:
        return False
    ru_low = ru.lower()
    en_low = en.lower()
    if (
        re.search(r'(?:объясни|грамматик|предложен|перевед|как сказать|по-английски)', ru_low)
        and re.search(r'(?:explain|grammar|sentence|translate)', en_low)
    ):
        return True
    if looks_like_english_speech_misheard_as_russian(ru, en):
        return False
    if looks_like_transliterated_russian(en):
        return False
    phonetic_hits = sum(
        1 for w in en.split() if looks_like_phonetic_russian_latin(_bare_word(w))
    )
    if phonetic_hits >= 1:
        return False
    if _english_frame_needs_russian_words(en):
        return False
    if _en_pass_has_real_english_frame(en) and _parallel_hint_score(ru, en) >= 2:
        return False
    return True


def is_pure_russian_speech(ru: str, en: str) -> bool:
    """Learner spoke Russian; EN pass is junk or a phonetic duplicate — use RU only."""
    ru = (ru or '').strip()
    if not ru or not _has_cyrillic(ru):
        return False
    ru_words = re.findall(r'[а-яё]+', ru.lower())
    if not ru_words:
        return False
    en = (en or '').strip()
    if not en:
        return True
    if _has_cyrillic(en) and not _has_cyrillic(ru):
        return False
    if _prefer_russian_over_en_translation(ru, en):
        return True
    if _en_pass_has_real_english_frame(en):
        return False
    if _clean_russian_utterance(ru) and _has_slavic_stt_junk_en_pass(en):
        return True
    if looks_like_transliterated_russian(en) or lacks_english_content(en):
        return True
    en_best = _pick_english_fragment(normalize_english_fragment(en))
    return not en_best or not is_meaningful_english_fragment(en_best)


def merge_code_switch_transcript(ru: str, en: str) -> str:
    """User spoke English but inserted Russian words they forgot in English."""
    en = collapse_voice_fillers(en or '')
    ru = collapse_voice_fillers(ru or '')
    if is_pure_russian_speech(ru, en):
        return ''
    prefix, question = split_trailing_english_question(en)
    work_en = prefix or en

    phonetic_hits = sum(
        1 for w in work_en.split() if looks_like_phonetic_russian_latin(_bare_word(w))
    )
    ru_forgotten = _extract_ru_forgotten_words(ru)

    if _english_frame_needs_russian_words(work_en) and ru_forgotten:
        scaffold = _scaffold_english_lead_in(work_en)
        forgotten = _filter_forgotten_words(ru_forgotten, work_en)
        if scaffold and forgotten:
            result = f'{scaffold}\n(забыл слова: {", ".join(forgotten)})'
            if question:
                result += f'\n{normalize_voice_english_transcript(question)}'
            return result

    like_sc = scaffold_i_like_to(work_en)
    if like_sc:
        if ru and not is_code_switch_message(like_sc):
            return f'{ru}\n{like_sc}'
        return like_sc

    scaffold = _english_scaffold_from_en(work_en)
    if ru_forgotten and phonetic_hits < 1:
        frame_scaffold = _scaffold_i_want_to_channel(work_en)
        if '…' in frame_scaffold:
            scaffold = frame_scaffold

    if phonetic_hits < 1 and not ru_forgotten:
        return ''
    if phonetic_hits < 1 and '…' not in scaffold:
        if ru_forgotten:
            gap_scaffold = scaffold_i_want_to_english_goal(work_en)
            if not gap_scaffold or '…' not in gap_scaffold:
                if _english_frame_needs_russian_words(work_en):
                    gap_scaffold = _scaffold_english_lead_in(work_en)
                elif re.search(r'\bi want to\s+my\s+english\s+channel\b', work_en, re.I):
                    gap_scaffold = normalize_voice_english_transcript(
                        re.sub(r'(\bi want to)\s+', r'\1 … ', work_en, count=1, flags=re.I),
                    )
            if gap_scaffold and '…' in gap_scaffold:
                scaffold = gap_scaffold
        if '…' not in scaffold:
            return ''
    if not scaffold and not ru_forgotten:
        return ''

    forgotten = ru_forgotten
    if not forgotten:
        forgotten = [
            _PHONETIC_RU_LATIN_HINTS.get(_bare_word(w), w)
            for w in work_en.split()
            if looks_like_phonetic_russian_latin(_bare_word(w))
        ]
    en_context = ' '.join(x for x in (work_en, scaffold, question) if x)
    forgotten = _filter_forgotten_words(forgotten, en_context)
    if forgotten and scaffold:
        result = f'{scaffold}\n(забыл слова: {", ".join(forgotten)})'
        if question:
            result += f'\n{normalize_voice_english_transcript(question)}'
        return result
    return scaffold or ru


def is_code_switch_message(text: str) -> bool:
    t = (text or '').strip().lower()
    return '(забыл слова:' in t or '(забыл слово:' in t


def prepare_tutor_voice_transcript(text: str) -> str:
    """Normalize bilingual tutor transcript after voice STT."""
    text = (text or '').strip()
    if not text:
        return ''
    if is_code_switch_message(text):
        head, tail = text.split('\n(', 1)
        body = f'{normalize_voice_english_transcript(head.strip())}\n({tail}'
        lines = body.split('\n')
        out = [lines[0]]
        for line in lines[1:]:
            if line.strip().startswith('(забыл'):
                out.append(line)
            elif line.strip():
                out.append(normalize_voice_english_transcript(line))
        return '\n'.join(out)
    if '\n' in text:
        ru_part, en_part = text.split('\n', 1)
        en_clean = normalize_voice_english_transcript(en_part)
        if ru_part.strip() and en_clean:
            return f'{ru_part.strip()}\n{en_clean}'
        return en_clean or ru_part.strip()
    if _has_cyrillic(text):
        return text
    cleaned = normalize_voice_english_transcript(text)
    return sanitize_stt_garbage_clauses(cleaned)


def split_cyrillic_mixed_transcript(text: str) -> tuple[str, str]:
    """Split RU STT line into Russian text + English recovered from Cyrillic phonetics."""
    if not text or not _has_cyrillic(text):
        return (text or '').strip(), ''

    tokens = _tokenize(text)
    ru_tokens: list[str] = []
    en_start = len(tokens)

    for i, raw in enumerate(tokens):
        word = _bare_word(raw)
        if not word:
            continue
        if is_cyrillic_phonetic_english(word):
            en_start = i
            break
        if word == 'вот' and i + 1 < len(tokens):
            if is_cyrillic_phonetic_english(tokens[i + 1]):
                en_start = i
                break
        ru_tokens.append(raw)

    ru_part = ' '.join(ru_tokens).strip()
    if en_start >= len(tokens):
        return ru_part, ''

    en_phonetic = ' '.join(_bare_word(t) for t in tokens[en_start:])
    en_latin = _format_english_display(decyrillify_english_phonetic(en_phonetic))
    return ru_part, en_latin


def _en_pass_relates_to_phonetic(phonetic: str, en_raw: str) -> bool:
    if not phonetic or not en_raw:
        return False
    p = phonetic.lower()
    e = normalize_english_fragment(en_raw).lower()
    return p in e or e in p


def looks_like_transliterated_russian(text: str) -> bool:
    """True when Latin text is likely Russian mis-heard by an EN STT model."""
    if not text or _has_cyrillic(text):
        return False
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return False
    hits = sum(1 for w in words if w in _RU_PHONETIC_LATIN)
    if hits >= 2:
        return True
    if hits >= 1 and hits / len(words) >= 0.2:
        return True
    long_weird = sum(1 for w in words if len(w) >= 11)
    return long_weird >= 1 and hits >= 1


def is_meaningful_english_fragment(text: str) -> bool:
    """True when Latin text looks like real English, not STT noise."""
    text = normalize_english_fragment((text or '').strip())
    if not text or is_garbage_transcript(text) or looks_like_transliterated_russian(text):
        return False
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return False
    unique = set(words)
    if len(words) >= 3 and len(unique) == 1 and words[0] in _FILLER_EN:
        return False
    substantive = [w for w in words if w not in _FILLER_EN and len(w) >= 3]
    if substantive:
        return True
    if len(words) >= 2 and len(unique) >= 2:
        return any(len(w) >= 4 for w in words)
    return text.lower() in {"i'm", "i'll", "how are you", "what is it"}


def extract_english_clause(text: str) -> str:
    """Pull the English fragment from a mixed / mis-transcribed line."""
    if not text:
        return ''
    low = text.lower()
    for starter in (
        'what ', 'how ', 'why ', 'when ', 'where ', 'who ', 'can you ',
        'could you ', 'can we ', 'can i ', 'i feel', 'i am ', "i'm ", "i'll ",
        'do you ', 'are you ', 'would you ',
    ):
        idx = low.find(starter)
        if idx >= 0:
            fragment = normalize_english_fragment(text[idx:].strip().strip('«»"'))
            return fragment if is_meaningful_english_fragment(fragment) else ''

    kept: list[str] = []
    for raw in text.split():
        clean = re.sub(r"[^\w']", '', raw.lower())
        if not clean:
            continue
        if clean in _COMMON_EN:
            kept.append(raw)
            continue
        if len(clean) >= 4 and clean.endswith(('ing', 'ed', 'ly', 'tion', 'ness')):
            kept.append(raw)
    fragment = normalize_english_fragment(' '.join(kept).strip())
    return fragment if is_meaningful_english_fragment(fragment) else ''


def merge_english_with_embedded_russian(en: str) -> str:
    """English sentence with Cyrillic gap-words the learner inserted in Russian."""
    en = (en or '').strip()
    if not en or not _has_cyrillic(en):
        return ''
    cyrillic_words = [
        w for w in re.findall(r'[А-Яа-яЁё]+', en)
        if w.lower() not in _RU_SKIP_IN_FORGOTTEN and len(w) >= 3
    ]
    en_frame = re.sub(r'[А-Яа-яЁё]+', '…', en)
    en_frame = re.sub(r'(\s*…\s*)+', ' … ', en_frame).strip()
    en_frame = normalize_voice_english_transcript(en_frame)
    if not en_frame or not re.search(r'[a-z]', en_frame, re.I):
        return ''
    if not is_meaningful_english_fragment(en_frame.replace('…', 'word')):
        return ''
    if not cyrillic_words:
        return en_frame
    label = 'забыл слово' if len(cyrillic_words) == 1 else 'забыл слова'
    seen: set[str] = set()
    unique = [w for w in cyrillic_words if w not in seen and not seen.add(w)]  # type: ignore[func-returns-value]
    return f'{en_frame}\n({label}: {", ".join(unique)})'


def is_ru_phantom_of_english_speech(ru: str, en: str) -> bool:
    """RU pass is a mis-hearing of the same English audio — do not show both."""
    ru = (ru or '').strip()
    en_best = _pick_english_fragment(normalize_english_fragment(en or ''))
    if not ru or not en_best or not _has_cyrillic(ru):
        return False
    if not is_meaningful_english_fragment(en_best):
        return False
    en_low = en_best.lower()
    if not re.search(
        r'\b(i would like|i want to|i love to|i like to|i have|i am|i\'m)\b',
        en_low,
    ):
        return False
    if _has_cyrillic(en or ''):
        return True
    if _parallel_hint_score(ru, en_best) >= 1:
        return True
    if 'travel' in en_low and re.search(r'путешеств', ru.lower()):
        return True
    en_words = re.findall(r"[a-z']+", en_low)
    return len(en_words) >= 5


def _pick_english_fragment(*candidates: str) -> str:
    best = ''
    best_score = -1
    for raw in candidates:
        text = normalize_english_fragment((raw or '').strip())
        if not is_meaningful_english_fragment(text):
            continue
        words = re.findall(r"[a-z']+", text.lower())
        score = len(words) + sum(1 for w in words if w in _COMMON_EN) * 2
        if score > best_score:
            best_score = score
            best = text
    return best


def _parallel_hint_score(ru: str, en: str) -> int:
    ru_low = (ru or '').lower()
    en_low = (en or '').lower()
    return sum(
        1 for ru_frag, en_frag in _RU_EN_PARALLEL_HINTS
        if ru_frag in ru_low and en_frag in en_low
    )


def _ru_has_real_russian_markers(ru: str) -> bool:
    words = re.findall(r'[а-яё]+', (ru or '').lower())
    if not words:
        return False
    if any(w in _RU_REAL_SPEECH_MARKERS for w in words):
        return True
    return any(
        len(w) >= 5 and w.endswith(('ать', 'ить', 'еть', 'ция', 'ость', 'ский', 'ская', 'ные', 'ный'))
        for w in words
    )


def should_drop_ru_pass_as_english_phantom(ru: str, en: str) -> bool:
    """RU pass invented Cyrillic garbage while EN pass got real English."""
    ru = (ru or '').strip()
    en_best = _pick_english_fragment(normalize_english_fragment(en or ''))
    if not ru or not en_best or not _has_cyrillic(ru):
        return False
    if not is_meaningful_english_fragment(en_best):
        return False
    en_words = re.findall(r"[a-z']+", en_best.lower())
    if len(en_words) < 4:
        return False
    if _ru_has_real_russian_markers(ru):
        return False
    _, en_from_ru = split_cyrillic_mixed_transcript(ru)
    if en_from_ru:
        return False
    return True


def looks_like_english_speech_misheard_as_russian(ru: str, en: str) -> bool:
    """EN pass got real English but RU pass turned the same audio into Russian."""
    ru = (ru or '').strip()
    en_best = _pick_english_fragment(normalize_english_fragment(en or ''))
    if not ru or not en_best or not _has_cyrillic(ru):
        return False
    _, en_from_ru = split_cyrillic_mixed_transcript(ru)
    if en_from_ru:
        return False
    if looks_like_transliterated_russian(en or ''):
        return False
    score = _parallel_hint_score(ru, en_best)
    if score >= 2:
        return True
    en_words = re.findall(r"[a-z']+", en_best.lower())
    return score >= 1 and len(en_words) >= 5


def merge_tutor_transcripts(ru: str, en: str) -> str:
    """Combine RU + EN STT into one message for the tutor."""
    ru = (ru or '').strip()
    en = (en or '').strip()

    if _both_passes_same_english(ru, en):
        return normalize_voice_english_transcript(en or ru)

    if is_pure_russian_speech(ru, en):
        ru_clean, en_from_ru = split_cyrillic_mixed_transcript(ru)
        if en_from_ru and ru_clean:
            return f'{ru_clean}\n{en_from_ru}'
        if en_from_ru:
            return en_from_ru
        return ru_clean or ru

    code_switch = merge_code_switch_transcript(ru, en)
    if code_switch:
        return code_switch

    embedded_en = merge_english_with_embedded_russian(en)
    if embedded_en:
        return embedded_en

    if not ru and en:
        en_only = scaffold_i_like_to(en) or merge_code_switch_transcript('', en)
        if en_only:
            return en_only

    if is_garbage_transcript(ru):
        ru = ''
    if is_garbage_transcript(en):
        en = ''

    phonetic_only = phonetic_english_only_line(ru)
    if phonetic_only:
        en_raw = normalize_english_fragment(en)
        if en_raw and _en_pass_relates_to_phonetic(phonetic_only, en_raw):
            return _pick_english_fragment(phonetic_only, en_raw) or phonetic_only
        return phonetic_only

    ru_clean, en_from_ru = split_cyrillic_mixed_transcript(ru)
    en_from_en = extract_english_clause(en) if en else ''
    en_final = _pick_english_fragment(
        en_from_ru,
        en_from_en,
        normalize_english_fragment(en),
    )

    if (
        looks_like_english_speech_misheard_as_russian(ru_clean, en)
        or should_drop_ru_pass_as_english_phantom(ru_clean, en)
        or is_ru_phantom_of_english_speech(ru_clean, en)
    ):
        phantom_merge = merge_english_with_embedded_russian(en) or en_final
        return phantom_merge

    if ru_clean and en_final:
        return f'{ru_clean}\n{en_final}'
    if ru_clean:
        return ru_clean
    if en_final:
        return en_final
    if en and is_meaningful_english_fragment(en):
        return normalize_english_fragment(en)
    return ru or en


def tutor_transcript_label(text: str) -> str:
    """User-facing prefix for what was heard — one clear line, not RU/EN dual dumps."""
    if not text:
        return ''
    if is_code_switch_message(text):
        lines = text.split('\n')
        head = lines[0].strip()
        forgotten = ''
        extras: list[str] = []
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('(забыл'):
                forgotten = stripped.replace('(забыл слова:', '').replace('(забыл слово:', '').rstrip(')').strip()
            elif stripped:
                extras.append(stripped)
        out = [f'🎙️ Услышал: «{head}»']
        if forgotten:
            out.append(f'💡 Забыл по-английски: {forgotten}')
        for extra in extras:
            out.append(f'❓ «{extra}»')
        return '\n'.join(out)
    if '\n' in text:
        ru_part, en_part = text.split('\n', 1)
        if is_meaningful_english_fragment(en_part):
            return f'🎙️ Услышал: «{en_part.strip()}»'
        if _has_cyrillic(ru_part):
            return f'🎙️ Услышал (по-русски): «{ru_part.strip()}»'
    if _has_cyrillic(text):
        return f'🎙️ Услышал (по-русски): «{text}»'
    return f'🎙️ Услышал: «{text}»'


def english_portion_for_tutor(text: str, *, from_voice: bool = False) -> str:
    """English fragment to send to the tutor for grammar analysis."""
    text = (text or '').strip()
    if not text:
        return ''
    if is_code_switch_message(text):
        parts = [text.split('\n', 1)[0].strip()]
        for line in text.split('\n')[1:]:
            stripped = line.strip()
            if stripped.startswith('(забыл'):
                continue
            if stripped:
                parts.append(stripped)
        portion = ' '.join(parts)
    elif '\n' in text:
        portion = text.split('\n', 1)[1].strip()
    elif _has_cyrillic(text):
        return ''
    else:
        portion = text
    portion = normalize_english_fragment(portion)
    if from_voice:
        portion = normalize_voice_english_transcript(portion)
    return portion
