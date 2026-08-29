#!/usr/bin/env python
"""One-off full bank scan — run on server via manage.py shell."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from collections import defaultdict

from learning.models import WordBankEntry
from learning.english_display import ALWAYS_CAP, display_word_fields
from learning.word_bank.translation_enrich import _translation_has_english_noise, sanitize_translation_for_display
from learning.word_bank.word_quality import is_acceptable_headword

issues = defaultdict(list)
counts = defaultdict(int)

for e in WordBankEntry.objects.filter(is_active=True).iterator():
    en = (e.english or '').strip()
    ru = (e.translation or '').strip()
    low = en.lower()
    lvl = e.cefr_level

    if not is_acceptable_headword(en, ru, part_of_speech=e.part_of_speech or ''):
        counts['junk'] += 1
        issues['junk'].append(f'{lvl}:{en} — {ru[:60]}')

    if len(low) <= 3 and low not in {'ok', 'tv', 'pc', 'id', 'uk', 'us', 'eu', 'ai', 'it', 'pm', 'am', 'act', 'add', 'age', 'air', 'all', 'and', 'any', 'are', 'art', 'ask', 'bad', 'bag', 'bar', 'bed', 'big', 'bit', 'box', 'boy', 'bus', 'but', 'buy', 'can', 'car', 'cat', 'cup', 'cut', 'day', 'did', 'dog', 'dry', 'due', 'ear', 'eat', 'egg', 'end', 'eye', 'far', 'few', 'fit', 'fly', 'for', 'fun', 'gap', 'gas', 'get', 'god', 'got', 'guy', 'had', 'has', 'hat', 'her', 'him', 'his', 'hit', 'hot', 'how', 'ice', 'ill', 'its', 'job', 'joy', 'key', 'kid', 'law', 'lay', 'leg', 'let', 'lie', 'lip', 'log', 'lot', 'low', 'mad', 'man', 'map', 'may', 'men', 'met', 'mix', 'mom', 'mud', 'net', 'new', 'nor', 'not', 'now', 'num', 'nut', 'off', 'oil', 'old', 'one', 'our', 'out', 'own', 'pay', 'pen', 'pet', 'pie', 'pig', 'pin', 'pop', 'pot', 'put', 'ran', 'raw', 'red', 'row', 'run', 'sad', 'say', 'sea', 'see', 'set', 'she', 'sin', 'sir', 'sit', 'six', 'sky', 'son', 'sun', 'tab', 'tag', 'tax', 'tea', 'ten', 'the', 'tie', 'tip', 'toe', 'too', 'top', 'toy', 'try', 'two', 'use', 'van', 'war', 'was', 'way', 'web', 'wet', 'who', 'why', 'win', 'won', 'yes', 'yet', 'you', 'zoo'}:
        if len(low) <= 3:
            counts['short3'] += 1
            issues['short3'].append(f'{lvl}:{en} — {ru[:60]}')

    if _translation_has_english_noise(ru):
        counts['en_noise'] += 1
        issues['en_noise'].append(f'{lvl}:{en} — {ru[:80]}')

    if '(TR!)' in ru or '(tr!)' in ru.lower():
        counts['tr_marker'] += 1
        issues['tr_marker'].append(f'{lvl}:{en} — {ru[:80]}')

    clean = sanitize_translation_for_display(ru, english=en, part_of_speech=e.part_of_speech or '')
    if clean != ru and clean:
        counts['dirty_translation'] += 1
        if len(issues['dirty_translation']) < 40:
            issues['dirty_translation'].append(f'{lvl}:{en} | {ru[:50]} → {clean[:50]}')

    if low in ALWAYS_CAP and low == en.lower() and en != display_word_fields(english=en, translation=ru, part_of_speech=e.part_of_speech or '')['english']:
        counts['needs_cap'] += 1

    if low in ALWAYS_CAP and 'нас' in ru.lower() and low == 'us':
        counts['bad_us'] += 1
        issues['bad_us'].append(f'{lvl}:{en} — {ru}')

print('ACTIVE', WordBankEntry.objects.filter(is_active=True).count())
for k in sorted(counts):
    print(f'\n== {k} ({counts[k]}) ==')
    for line in issues[k][:20]:
        print(' ', line)
    if counts[k] > 20:
        print(f'  ... +{counts[k]-20} more')
