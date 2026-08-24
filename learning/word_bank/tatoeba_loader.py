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


def _stream_en_sentences(raw: bytes):
    with bz2.open(io.BytesIO(raw), 'rt', encoding='utf-8') as fh:
        for line in fh:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 3:
                continue
            try:
                sid = int(parts[0])
            except ValueError:
                continue
            text = parts[2].strip()
            if text:
                yield sid, text


def _load_ru_sentences(raw: bytes, wanted_ids: set[int]) -> dict[int, str]:
    out: dict[int, str] = {}
    if not wanted_ids:
        return out
    with bz2.open(io.BytesIO(raw), 'rt', encoding='utf-8') as fh:
        for line in fh:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 3:
                continue
            try:
                sid = int(parts[0])
            except ValueError:
                continue
            if sid not in wanted_ids:
                continue
            text = parts[2].strip()
            if text:
                out[sid] = text
            if len(out) >= len(wanted_ids):
                break
    return out


def cache_tatoeba_examples(path: Path, *, headwords: list[str]) -> dict[str, dict[str, str]]:
    """Match Tatoeba EN sentences to bank headwords without loading the full corpus."""
    targets = {h.lower() for h in headwords if h.strip()}
    if not targets:
        return {}

    best: dict[str, tuple[tuple[int, int], str, int]] = {}

    for en_id, en_text in _stream_en_sentences(_fetch_bytes(TATOEBA_EN_URL)):
        matched = _sentence_tokens(en_text) & targets
        if not matched:
            continue
        for hw in matched:
            score = _score_sentence(en_text, hw)
            if score[0] >= 998:
                continue
            prev = best.get(hw)
            if prev is None or score < prev[0]:
                best[hw] = (score, en_text, en_id)

    en_ids = {item[2] for item in best.values()}
    ru_by_en: dict[int, int] = {}
    with tarfile.open(
        fileobj=io.BytesIO(_fetch_bytes(TATOEBA_LINKS_URL)),
        mode='r:bz2',
    ) as tf:
        member = next(
            (m for m in tf.getmembers() if m.name.endswith('links.csv')),
            None,
        )
        if member is not None:
            fh = tf.extractfile(member)
            if fh is not None:
                reader = csv.reader(
                    io.TextIOWrapper(fh, encoding='utf-8'),
                    delimiter='\t',
                )
                for row in reader:
                    if len(row) < 2:
                        continue
                    try:
                        a, b = int(row[0]), int(row[1])
                    except ValueError:
                        continue
                    if a in en_ids:
                        ru_by_en[a] = b
                    elif b in en_ids:
                        ru_by_en[b] = a

    ru_ids = set(ru_by_en.values())
    ru_sentences = _load_ru_sentences(_fetch_bytes(TATOEBA_RU_URL), ru_ids)

    lookup: dict[str, dict[str, str]] = {}
    for hw, (_score, en_text, en_id) in best.items():
        ru_id = ru_by_en.get(en_id)
        if not ru_id:
            continue
        ru_text = ru_sentences.get(ru_id, '')
        if not ru_text:
            continue
        lookup[hw] = {'example': en_text, 'example_ru': ru_text}

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
