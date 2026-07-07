import asyncio
import os
import sys

os.chdir('/home/mentor/english-mentor-bot')
sys.path.insert(0, '/home/mentor/english-mentor-bot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from ai_app.speech import get_stt_provider, get_tutor_stt_provider


async def main():
  for label, provider in (
      ('global', get_stt_provider()),
      ('tutor', get_tutor_stt_provider(stt_model='whisper-large-v3-turbo')),
  ):
      print(label, 'provider:', provider.name)


asyncio.run(main())
