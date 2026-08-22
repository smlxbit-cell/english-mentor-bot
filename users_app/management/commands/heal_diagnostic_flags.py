from django.core.management.base import BaseCommand

from users_app.models import UserProfile


class Command(BaseCommand):
    help = 'Set diagnostic_completed=True where level/onboarding exist but flag is false.'

    def handle(self, *args, **options):
        qs = UserProfile.objects.filter(
            diagnostic_completed=False,
            cefr_level__gt='',
        )
        n = qs.update(diagnostic_completed=True)
        self.stdout.write(self.style.SUCCESS(f'Healed {n} profile(s) with cefr_level set.'))

        qs2 = UserProfile.objects.filter(
            diagnostic_completed=False,
            onboarding_status='completed',
        )
        n2 = qs2.update(diagnostic_completed=True)
        self.stdout.write(self.style.SUCCESS(f'Healed {n2} profile(s) with onboarding completed.'))
