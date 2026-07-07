"""One-off: clear Telegram webhook so polling works."""
import asyncio
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from telegram import Bot


async def main():
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    info = await bot.get_webhook_info()
    print('webhook:', info.url or '(none)')
    await bot.delete_webhook(drop_pending_updates=True)
    print('webhook cleared, pending updates dropped')


asyncio.run(main())
