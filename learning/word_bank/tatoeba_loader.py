"""Build EN↔RU usage examples from Tatoeba exports."""

from __future__ import annotations

import bz2
import csv
import io
import json
import re
import tarfile
import urllib.request
from pathlib import Path

TATOEBA_EN_URL = 'https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2'
TATOEBA_RU_URL = 'https://downloads.tatoeba.org/exports/per_language/rus/rus_sentences.tsv.bz2'
TATOEBA_LINKS_URL = 'https://downloads.tatoeba.org/exports/links.tar.bz2'
CACHE_FILENAME = 'tatoeba_examples.json'

_WORD_RE = re.compile(r"[a-z']{2,}")
_BAD_SENTENCE_RE = re.compile(
    r'^(?:yes|no|ok|hello|thanks|please|sorry)[.!?]?$',
    re.I,
)


def _fetch_bytes(url: str, *, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'english-mentor-bot/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _read_tatoeba_sentences(raw: bytes) -> dict[int, str]:
    out: dict[int, str] = {}
    with bz2.open(io.BytesIO(raw), 'rt', encoding='utf-8') as fh:
        for line in fh:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 3:
                continue
            sid = int(parts[0])
            text = parts[2].strip()
            if text:
                out[sid] = text
    return out


def _read_tatoeba_links(raw: bytes) -> dict[int, int]:
    links: dict[int, int] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:bz2') as tf:
        member = next(
            (m for m in tf.getmembers() if m.name.endswith('links.csv')),
            None,
        )
        if member is None:
            return links
        fh = tf.extractfile(member)
        if fh is None:
            return links
        reader = csv.reader(io.TextIOWrapper(fh, encoding='utf-8'), delimiter='\t')
        for row in reader:
            if len(row) < 2:
                continue
            try:
                a, b = int(row[0]), int(row[1])
            except ValueError:
                continue
            links.setdefault(a, b)
            links.setdefault(b, a)
    return links


def _sentence_tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _WORD_RE.finditer(text)}


def _score_sentence(text: str, headword: str) -> tuple[int, int]:
    hw = headword.lower()
    if not re.search(rf'\b{re.escape(hw)}\b', text, re.I):
        return (999, 999)
    if _BAD_SENTENCE_RE.match(text.strip()):
        return (998, len(text))
    words = text.split()
    penalty = 0
    if text.count('"') >= 2:
        penalty += 3
    if len(words) < 4:
        penalty += 4
    if len(words) > 18:
        penalty += len(words) - 18
    if text.strip().endswith('?'):
        penalty += 1
    return (penalty, len(text))


def _build_word_index(
    en_sentences: dict[int, str],
    ru_sentences: dict[int, str],
    links: dict[int, int],
) -> dict[str, list[tuple[str, str]]]:
    by_word: dict[str, list[tuple[str, str, tuple[int, int]]]] = {}
    for en_id, en_text in en_sentences.items():
        ru_id = links.get(en_id)
        if not ru_id:
            continue
        ru_text = ru_sentences.get(ru_id, '')
        if not ru_text:
            continue
        for token in _sentence_tokens(en_text):
            score = _score_sentence(en_text, token)
            if score[0] >= 998:
                continue
            by_word.setdefault(token, []).append((en_text, ru_text, score))

    index: dict[str, list[tuple[str, str]]] = {}
    for word, rows in by_word.items():
        rows.sort(key=lambda item: (item[2], len(item[0])))
        seen: set[str] = set()
        cleaned: list[tuple[str, str]] = []
        for en_text, ru_text, _score in rows:
            key = en_text.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append((en_text, ru_text))
            if len(cleaned) >= 3:
                break
        if cleaned:
            index[word] = cleaned
    return index


def cache_tatoeba_examples(path: Path, *, headwords: list[str]) -> dict[str, dict[str, str]]:
    en_sentences = _read_tatoeba_sentences(_fetch_bytes(TATOEBA_EN_URL))
    ru_sentences = _read_tatoeba_sentences(_fetch_bytes(TATOEBA_RU_URL))
    links = _read_tatoeba_links(_fetch_bytes(TATOEBA_LINKS_URL))
    index = _build_word_index(en_sentences, ru_sentences, links)

    lookup: dict[str, dict[str, str]] = {}
    for headword in headwords:
        rows = index.get(headword.lower())
        if not rows:
            continue
        en_text, ru_text = rows[0]
        lookup[headword.lower()] = {'example': en_text, 'example_ru': ru_text}

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lookup, ensure_ascii=False, indent=0), encoding='utf-8')
    return lookup


def load_tatoeba_examples(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return {}
    return {
        str(k).lower(): {
            'example': str(v.get('example', '')).strip(),
            'example_ru': str(v.get('example_ru', '')).strip(),
        }
        for k, v in data.items()
        if isinstance(v, dict)
    }
