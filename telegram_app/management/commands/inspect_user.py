"""Inspect a Telegram user profile (owner debugging)."""

from django.core.management.base import BaseCommand

from billing_app.models import Payment, Subscription
from billing_app.trial_access import access_tier_label, trial_days_remaining
from study_app.models import LessonProgress, StepAttempt
from users_app.models import UserProfile


class Command(BaseCommand):
    help = 'Show profile details for all or one telegram user.'

    def add_arguments(self, parser):
        parser.add_argument('telegram_id', nargs='?', type=int, help='Optional telegram id')

    def handle(self, *args, **options):
        tid = options.get('telegram_id')
        qs = UserProfile.objects.filter(telegram_id__isnull=False).order_by('-created_at')
        if tid:
            qs = qs.filter(telegram_id=tid)
        if not qs.exists():
            self.stdout.write('No users found.')
            return
        for p in qs:
            tier = access_tier_label(p)
            self.stdout.write('=' * 56)
            self.stdout.write(f'telegram_id: {p.telegram_id}')
            self.stdout.write(f'name: {p.first_name!r} {p.last_name!r}'.strip())
            self.stdout.write(f'username: @{p.telegram_username}' if p.telegram_username else 'username: —')
            self.stdout.write(f'created: {p.created_at:%Y-%m-%d %H:%M}')
            self.stdout.write(f'last_seen: {p.last_seen:%Y-%m-%d %H:%M}' if p.last_seen else 'last_seen: —')
            self.stdout.write(f'tier: {tier}' + (f' ({trial_days_remaining(p)}d left)' if tier == 'trial' else ''))
            self.stdout.write(f'trial_started: {p.trial_started_at:%Y-%m-%d %H:%M}' if p.trial_started_at else 'trial_started: —')
            self.stdout.write(
                f'onboarding: {p.onboarding_status} · diag={p.diagnostic_completed} · level={p.cefr_level or "—"}'
            )
            self.stdout.write(f'lessons: {LessonProgress.objects.filter(user=p).count()} · attempts: {StepAttempt.objects.filter(user=p).count()}')
            pay = Payment.objects.filter(user=p).order_by('-created_at').first()
            if pay:
                self.stdout.write(f'last payment: {pay.plan.code if pay.plan_id else "—"} {pay.amount_rub} RUB {pay.created_at:%d.%m %H:%M}')
            sub = Subscription.objects.filter(user=p).order_by('-expires_at').first()
            if sub:
                self.stdout.write(f'subscription: {sub.plan.code} {sub.status} until {sub.expires_at:%d.%m.%Y}')
