"""Download and parse FreeDict/WikDict eng-rus (StarDict) for richer translations."""

from __future__ import annotations

import gzip
import html
import io
import json
import re
import struct
import tarfile
import urllib.request
from pathlib import Path

FREEDICT_STARDICT_URL = (
    'https://download.freedict.org/dictionaries/eng-rus/2025.11.23/'
    'freedict-eng-rus-2025.11.23.stardict.tar.xz'
)
CACHE_FILENAME = 'freedict_ru.json'


def _fetch_bytes(url: str, *, timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'english-mentor-bot/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _html_to_text(body: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', body)
    text = re.sub(r'\s+', ' ', html.unescape(text)).strip()
    return text


def parse_stardict_archive(raw: bytes) -> dict[str, str]:
    """Return english headword (lower) → plain-text dictionary entry."""
    entries: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:xz') as tf:
        idx = gzip.decompress(tf.extractfile('eng-rus/eng-rus.idx.gz').read())
        dic = tf.extractfile('eng-rus/eng-rus.dict').read()
    i = 0
    while i < len(idx):
        j = idx.find(b'\x00', i)
        if j < 0:
            break
        word = idx[i:j].decode('utf-8', 'replace').lower()
        off = struct.unpack('>I', idx[j + 1:j + 5])[0]
        size = struct.unpack('>I', idx[j + 5:j + 9])[0]
        body = dic[off:off + size].decode('utf-8', 'replace')
        entries[word] = _html_to_text(body)
        i = j + 9
    return entries


def fetch_freedict_lookup(*, url: str = FREEDICT_STARDICT_URL) -> dict[str, str]:
    """Download eng-rus StarDict and return headword → entry text."""
    return parse_stardict_archive(_fetch_bytes(url))


def cache_freedict_lookup(path: Path, *, url: str = FREEDICT_STARDICT_URL) -> dict[str, str]:
    lookup = fetch_freedict_lookup(url=url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lookup, ensure_ascii=False, indent=0), encoding='utf-8')
    return lookup


def load_freedict_lookup(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path}: expected JSON object')
    return {str(k).lower(): str(v) for k, v in data.items()}
