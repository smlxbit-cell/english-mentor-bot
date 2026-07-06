"""Upload a circular video (video note) for a story character and save file_id.

Telegram caches file_id — upload once, reuse forever.

Example:
  python manage.py register_character_video --character Emma --file media/emma.mp4 --chat-id YOUR_TELEGRAM_ID
"""

from __future__ import annotations

import asyncio
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from config.settings import TELEGRAM_BOT_TOKEN
from telegram_app.bot.telegram_client import make_bot
from content_app.models import Character


class Command(BaseCommand):
    help = 'Upload a video note MP4 for a character and store telegram file_id.'

    def add_arguments(self, parser):
        parser.add_argument('--character', default='Emma', help='Character name')
        parser.add_argument('--file', required=True, help='Path to square MP4 (≤60s)')
        parser.add_argument(
            '--chat-id', type=int, required=True,
            help='Your Telegram user id (one-time upload target)',
        )

    def handle(self, *args, **options):
        if not TELEGRAM_BOT_TOKEN:
            raise CommandError('TELEGRAM_BOT_TOKEN is not set.')

        path = options['file']
        if not os.path.isabs(path):
            path = os.path.join(settings.BASE_DIR, path)
        if not os.path.isfile(path):
            raise CommandError(f'File not found: {path}')

        name = options['character']
        char = Character.objects.filter(name__iexact=name).first()
        if not char:
            raise CommandError(f'Character "{name}" not found. Run seed_content first.')

        file_id = asyncio.run(self._upload(path, options['chat_id']))
        char.video_note_file_id = file_id
        char.save(update_fields=['video_note_file_id'])
        self.stdout.write(self.style.SUCCESS(
            f'Saved video_note_file_id for {char.name}: {file_id[:40]}…',
        ))

    async def _upload(self, path: str, chat_id: int) -> str:
        bot = make_bot()
        with open(path, 'rb') as fh:
            msg = await bot.send_video_note(chat_id=chat_id, video_note=fh)
        if not msg.video_note:
            raise CommandError('Telegram did not return a video_note file_id.')
        return msg.video_note.file_id
