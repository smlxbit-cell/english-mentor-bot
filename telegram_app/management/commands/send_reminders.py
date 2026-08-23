"""Send daily training reminders to learners (run via cron every hour)."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import TELEGRAM_BOT_TOKEN
from study_app.daily_facts import format_compact_reminder
from telegram_app.bot import db
from telegram_app.bot.telegram_client import make_bot


class Command(BaseCommand):
    help = 'Send reminder messages to users whose reminder_time matches the current hour.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hour', type=int, default=None,
            help='Override hour (0-23) for testing',
        )
        parser.add_argument(
            '--minute', type=int, default=0,
            help='Minute to match (default 0)',
        )

    def handle(self, *args, **options):
        if not TELEGRAM_BOT_TOKEN:
            self.stderr.write('TELEGRAM_BOT_TOKEN is not set.')
            return

        now = timezone.localtime()
        hour = options['hour'] if options['hour'] is not None else now.hour
        minute = options['minute']

        import asyncio
        asyncio.run(self._send_all(hour, minute))

    async def _send_all(self, hour: int, minute: int):
        users = await db.users_due_reminder(hour, minute)
        if not users:
            self.stdout.write(f'No users due at {hour:02d}:{minute:02d}.')
            return

        bot = make_bot()
        sent = 0
        today = timezone.localdate()
        for u in users:
            plan = u['plan']
            payload = format_compact_reminder(u['profile_id'], today, plan)
            row = []
            if payload.get('tts_text'):
                row.append(InlineKeyboardButton('🔊 Слушать', callback_data='reminder:listen'))
            row.append(InlineKeyboardButton(
                payload.get('cta', '▶️ Начать'),
                callback_data='plan:continue',
            ))
            kb = InlineKeyboardMarkup([row])
            try:
                await bot.send_message(
                    chat_id=u['telegram_id'],
                    text=payload['text'],
                    reply_markup=kb,
                    parse_mode='HTML',
                )
                sent += 1
            except Exception as exc:
                self.stderr.write(f'Failed {u["telegram_id"]}: {exc}')

        self.stdout.write(self.style.SUCCESS(f'Sent {sent}/{len(users)} reminders.'))
