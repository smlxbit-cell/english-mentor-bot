from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run the English Mentor Telegram bot (polling).'

    def handle(self, *args, **options):
        # Imported here so Django apps are fully loaded before models are touched.
        from telegram_app.bot.handlers import build_application

        self.stdout.write(self.style.SUCCESS('English Mentor bot starting…'))
        application = build_application()
        application.run_polling()
