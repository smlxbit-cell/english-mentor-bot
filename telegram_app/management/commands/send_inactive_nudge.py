"""Proactive “we miss you” messages after 7+ days without a visit.

Run daily via cron, e.g. 10:00 Moscow:

    python manage.py send_inactive_nudge

Test without sending:

    python manage.py send_inactive_nudge --dry-run
"""

from __future__ import annotations

import asyncio

from django.core.management.base import BaseCommand
from django.utils import timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import TELEGRAM_BOT_TOKEN
from telegram_app.bot import db
from telegram_app.bot.telegram_client import make_bot
from telegram_app.inactive_tips import (
    INACTIVE_NUDGE_DAYS,
    days_label_ru,
    pick_inactive_tip,
)


class Command(BaseCommand):
    help = (
        'Send sleep-circle + tip to users who have not opened the bot '
        f'for {INACTIVE_NUDGE_DAYS}+ days.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=INACTIVE_NUDGE_DAYS,
            help=f'Days of inactivity (default {INACTIVE_NUDGE_DAYS})',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='List recipients without sending',
        )

    def handle(self, *args, **options):
        if not options['dry_run'] and not TELEGRAM_BOT_TOKEN:
            self.stderr.write('TELEGRAM_BOT_TOKEN is not set.')
            return

        users = db.users_due_inactive_nudge(days=options['days'])
        if not users:
            self.stdout.write(
                f'No users inactive {options["days"]}+ days (or already nudged).',
            )
            return

        if options['dry_run']:
            for u in users:
                self.stdout.write(
                    f'  {u["telegram_id"]}  {u["first_name"]}  '
                    f'away {u["days_away"]}d',
                )
            self.stdout.write(f'Would send {len(users)} nudge(s).')
            return

        asyncio.run(self._send_all(users))

    async def _send_all(self, users: list[dict]):
        bot = make_bot()
        clip = await db.get_character_media('Spirit', 'sleep')
        note_id = (clip or {}).get('note_file_id')
        sent = 0

        for u in users:
            name = u['first_name'] or 'друг'
            days = u['days_away']
            content = pick_inactive_tip(u['profile_id'], days)
            lines = [
                f'{name}, мы скучаем! 🌙',
                f'Тебя не было {days_label_ru(days)}.',
                '',
                f'💡 {content["tip"]}',
                '',
                f'✨ «{content["quote"]}»',
                f'🇬🇧 {content["en"]}',
                '',
                'Spirit ждёт — загляни хоть на 10 минут?',
            ]
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton('📚 Вернуться к учёбе', callback_data='plan:menu')],
            ])
            try:
                if note_id:
                    await bot.send_video_note(
                        chat_id=u['telegram_id'], video_note=note_id,
                    )
                await bot.send_message(
                    chat_id=u['telegram_id'],
                    text='\n'.join(lines),
                    reply_markup=kb,
                )
                db.mark_inactive_nudge_sent(u['profile_id'])
                sent += 1
                self.stdout.write(
                    f'  OK  {u["telegram_id"]} ({name}, {days}d away)',
                )
            except Exception as exc:
                self.stderr.write(f'Failed {u["telegram_id"]}: {exc}')

        self.stdout.write(self.style.SUCCESS(f'Sent {sent}/{len(users)} inactive nudges.'))
