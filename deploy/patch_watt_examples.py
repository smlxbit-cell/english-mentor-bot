#!/usr/bin/env python3
"""Manual examples for watt (AI fill keeps rejecting)."""
import json
from pathlib import Path

base = Path(__file__).resolve().parent.parent / 'learning' / 'data' / 'word_bank'
c1_path = base / 'c1_examples.json'
data = json.loads(c1_path.read_text(encoding='utf-8'))
data['watt'] = {
    'example': 'This device uses one watt of power.',
    'example_ru': 'Это устройство потребляет один ватт мощности.',
    'examples': [
        {
            'example': 'This device uses one watt of power.',
            'example_ru': 'Это устройство потребляет один ватт мощности.',
        },
        {
            'example': 'A ten-watt bulb is enough for a night light.',
            'example_ru': 'Для ночника достаточно лампочки на десять ватт.',
        },
        {
            'example': 'One watt is a unit of electrical power.',
            'example_ru': 'Один ватт — единица электрической мощности.',
        },
    ],
}
c1_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('patched c1_examples.json for watt')
