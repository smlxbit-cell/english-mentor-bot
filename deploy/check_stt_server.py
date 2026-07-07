import asyncio
import os
import sys

os.chdir('/home/mentor/english-mentor-bot')
sys.path.insert(0, '/home/mentor/english-mentor-bot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from ai_app.speech import get_stt_provider


async def test_provider(name):
    try:
        p = get_stt_provider(name)
        print(name, '->', p.name)
    except Exception as e:
        print(name, 'ERR', e)


async def main():
    for n in ('whisper', 'yandex'):
        await test_provider(n)
    from ai_app.speech.whisper import OpenAIWhisperSTT
    try:
        w = OpenAIWhisperSTT(model='whisper-large-v3-turbo')
        print('whisper model ok')
    except Exception as e:
        print('whisper init', e)


asyncio.run(main())
