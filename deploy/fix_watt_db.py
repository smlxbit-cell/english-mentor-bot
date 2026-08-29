#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()
from learning.models import WordBankEntry

examples = [
    {'example': 'This device uses one watt of power.', 'example_ru': 'Это устройство потребляет один ватт мощности.'},
    {'example': 'A ten-watt bulb is enough for a night light.', 'example_ru': 'Для ночника достаточно лампочки на десять ватт.'},
    {'example': 'One watt is a unit of electrical power.', 'example_ru': 'Один ватт — единица электрической мощности.'},
]
e = WordBankEntry.objects.filter(english__iexact='watt', is_active=True).first()
if e:
    e.example = examples[0]['example']
    e.example_ru = examples[0]['example_ru']
    e.extra_examples = examples[1:]
    e.save(update_fields=['example', 'example_ru', 'extra_examples', 'updated_at'])
    print('updated watt in DB')
else:
    print('watt not found')
