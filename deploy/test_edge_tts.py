import asyncio
import os
import sys

os.chdir('/home/mentor/english-mentor-bot')
sys.path.insert(0, '/home/mentor/english-mentor-bot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from ai_app.tts import get_tts_provider


async def main():
    p = get_tts_provider('edge')
    print('provider:', p.name)
    r = await p.synthesize('Hi! Are you new here?')
    print('ok:', r.ok, 'bytes:', len(r.audio or b''))


asyncio.run(main())
