import asyncio
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_app.tts import get_tts_provider


async def main():
    p = get_tts_provider()
    print('provider:', p.name)
    r = await p.synthesize('Hello, this is Spirit.')
    print('ok:', r.ok, 'bytes:', len(r.audio or b''))


asyncio.run(main())
