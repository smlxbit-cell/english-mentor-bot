"""Upload mentor GIF/photo/video for a character mood key.

Telegram caches file_id — upload once per asset.

Examples:
  python manage.py register_character_media --character Spirit --key greeting \\
      --file C:\\Users\\mariy\\Downloads\\Runway.mp4 --kind animation --chat-id YOUR_ID

Vertical video: prefer square crop (1:1) for animations; use --kind image for episode stills.
"""

from __future__ import annotations

import asyncio
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telegram import Bot

from config.settings import TELEGRAM_BOT_TOKEN
from content_app.models import Character, CharacterMedia


class Command(BaseCommand):
    help = 'Upload character media (GIF/MP4/photo) and store telegram file_id.'

    def add_arguments(self, parser):
        parser.add_argument('--character', default='Spirit')
        parser.add_argument('--key', required=True, help='greeting, joy, scene_cafe, …')
        parser.add_argument('--file', required=True, help='Path to GIF, MP4, JPG, or square MP4')
        parser.add_argument(
            '--kind',
            choices=['animation', 'image', 'video_note'],
            default='animation',
        )
        parser.add_argument('--title', default='')
        parser.add_argument('--chat-id', type=int, required=True)

    def handle(self, *args, **options):
        if not TELEGRAM_BOT_TOKEN:
            raise CommandError('TELEGRAM_BOT_TOKEN is not set.')

        path = options['file']
        if not os.path.isabs(path):
            path = os.path.join(settings.BASE_DIR, path)
        if not os.path.isfile(path):
            raise CommandError(f'File not found: {path}')

        char, _ = Character.objects.get_or_create(
            name=options['character'],
            defaults={
                'role': 'языковой дух — спутник ученика',
                'personality': 'warm, playful, encouraging, never judges mistakes',
                'speaking_style': 'short, friendly, simple English',
            },
        )

        file_id = asyncio.run(self._upload(path, options['chat_id'], options['kind']))
        clip, _ = CharacterMedia.objects.update_or_create(
            character=char,
            key=options['key'],
            defaults={
                'kind': options['kind'],
                'title': options['title'] or options['key'],
                'telegram_file_id': file_id,
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f'Saved {char.name}/{clip.key} ({clip.kind}) → {file_id[:48]}…',
        ))

    async def _upload(self, path: str, chat_id: int, kind: str) -> str:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        with open(path, 'rb') as fh:
            if kind == 'image':
                msg = await bot.send_photo(chat_id=chat_id, photo=fh)
                return msg.photo[-1].file_id
            if kind == 'video_note':
                msg = await bot.send_video_note(chat_id=chat_id, video_note=fh)
                if not msg.video_note:
                    raise CommandError('No video_note in response — use square 1:1 MP4.')
                return msg.video_note.file_id
            msg = await bot.send_animation(chat_id=chat_id, animation=fh)
            fid = (msg.animation or msg.video)
            if not fid:
                raise CommandError('Telegram did not return animation/video file_id.')
            return fid.file_id
