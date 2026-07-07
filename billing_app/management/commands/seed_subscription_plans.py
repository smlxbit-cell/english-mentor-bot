from django.core.management.base import BaseCommand

from billing_app.models import SubscriptionPlan
from billing_app.plans_catalog import PLANS


class Command(BaseCommand):
    help = 'Seed or update subscription plans from billing_app/plans_catalog.py'

    def handle(self, *args, **options):
        for spec in PLANS:
            plan, created = SubscriptionPlan.objects.update_or_create(
                code=spec['code'],
                defaults={
                    'name': spec['name'],
                    'price_rub': spec['price_rub'],
                    'duration_days': spec['duration_days'],
                    'plan_kind': spec['plan_kind'],
                    'voice_minutes_monthly': spec['voice_minutes_monthly'],
                    'voice_minutes_in_pack': spec['voice_minutes_in_pack'],
                    'tutor_ai_daily_limit': spec['tutor_ai_daily_limit'],
                    'tutor_ai_monthly_limit': spec['tutor_ai_monthly_limit'],
                    'stt_model': spec['stt_model'],
                    'description': spec['description'],
                    'sort_order': spec['sort_order'],
                    'is_active': True,
                },
            )
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'{verb}: {plan.code} — {plan.price_rub} ₽')
        self.stdout.write(self.style.SUCCESS('Done.'))
