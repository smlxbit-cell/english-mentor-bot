#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from content_app.models import Lesson
from telegram_app.bot.handlers import _speak_text_for_step

lesson = Lesson.objects.filter(title__icontains='Coffee').first()
if not lesson:
    print('NO_LESSON')
    sys.exit(1)

for s in lesson.steps.order_by('order')[:5]:
    step = {
        'step_type': s.step_type,
        'text': s.text,
        'title': s.title,
        'content': s.content or {},
    }
    gb = '\U0001f1ec\U0001f1e7'
    print(f'--- {s.step_type} ---')
    print('has_gb:', gb in (s.text or ''))
    print('speak:', repr(_speak_text_for_step(step)))
