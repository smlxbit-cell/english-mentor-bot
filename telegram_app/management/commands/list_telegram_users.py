"""List Telegram user IDs known to the bot (for sync_spirit_media --chat-id)."""

from django.core.management.base import BaseCommand

from users_app.models import UserProfile


class Command(BaseCommand):
    help = 'Show your Telegram numeric ID(s) saved after /start in the bot.'

    def handle(self, *args, **options):
        profiles = UserProfile.objects.filter(telegram_id__isnull=False).order_by(
            '-last_seen', '-id',
        )
        if not profiles:
            self.stdout.write(self.style.WARNING(
                'No users yet.\n'
                '1) Open @english_mentor_ai_bot in Telegram\n'
                '2) Press Start or send /start\n'
                '3) Run this command again\n'
                'Or message @userinfobot for your Id.',
            ))
            return

        self.stdout.write('Use one of these with sync_spirit_media --chat-id NUMBER:\n')
        for p in profiles:
            name = p.first_name or p.username or 'user'
            self.stdout.write(f'  {p.telegram_id}  —  {name}  (level {p.cefr_level or "?"})')
        self.stdout.write(
            '\nThen: python manage.py sync_spirit_media --chat-id YOUR_NUMBER\n'
            'Or just: python manage.py sync_spirit_media  (uses the first row above)',
        )
