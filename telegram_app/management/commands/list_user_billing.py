"""Overview of users: free / trial / paid — for owner reporting."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from billing_app.models import Payment, Subscription
from billing_app.trial_access import (
    access_tier_label,
    has_active_subscription,
    trial_days_remaining,
)
from users_app.models import UserProfile


class Command(BaseCommand):
    help = 'List Telegram users with billing tier (free / trial / paid).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--paid-only', action='store_true', help='Show only active subscribers.',
        )
        parser.add_argument(
            '--tier',
            choices=('free', 'trial', 'paid'),
            help='Filter by access tier.',
        )
        parser.add_argument(
            '--csv', action='store_true', help='Comma-separated output.',
        )
        parser.add_argument(
            '--limit', type=int, default=0, help='Max rows (0 = all).',
        )

    def handle(self, *args, **options):
        qs = UserProfile.objects.filter(telegram_id__isnull=False).order_by('-last_seen')
        if options['paid_only']:
            paid_ids = Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                expires_at__gt=timezone.now(),
            ).values_list('user_id', flat=True)
            qs = qs.filter(id__in=paid_ids)

        rows: list[str] = []
        shown = 0
        limit = options['limit'] or 0

        for p in qs.iterator():
            tier = access_tier_label(p)
            if options['tier'] and tier != options['tier']:
                continue
            paid_ever = Payment.objects.filter(
                user_id=p.id, status=Payment.Status.SUCCEEDED,
            ).exists()
            sub = Subscription.objects.filter(
                user_id=p.id,
                status=Subscription.Status.ACTIVE,
                expires_at__gt=timezone.now(),
            ).order_by('-expires_at').select_related('plan').first()
            sub_line = ''
            if sub:
                sub_line = f'{sub.plan.code} до {sub.expires_at:%d.%m.%Y}'
            name = (p.first_name or p.telegram_username or '—')[:16]
            seen = p.last_seen.strftime('%d.%m %H:%M') if p.last_seen else '—'
            if options['csv']:
                rows.append(
                    f'{p.telegram_id},{name},{p.cefr_level or ""},{tier},'
                    f'{"yes" if paid_ever else "no"},{sub_line},{seen}'
                )
            else:
                extra = ''
                if tier == 'trial':
                    extra = f' · trial {trial_days_remaining(p)}d'
                elif tier == 'paid' and sub:
                    extra = f' · {sub_line}'
                rows.append(
                    f'{p.telegram_id:>12}  {name:<16}  {p.cefr_level or "—":<4}  '
                    f'{tier:<5}  paid={"yes" if paid_ever else "no":<3}  '
                    f'seen {seen}{extra}'
                )
            shown += 1
            if limit and shown >= limit:
                break

        if not rows:
            self.stdout.write('No users found.')
            return

        if not options['csv']:
            self.stdout.write(
                f'{"telegram_id":>12}  {"name":<16}  lvl   tier   paid  last_seen'
            )
            self.stdout.write('-' * 72)
        for line in rows:
            self.stdout.write(line)

        all_qs = UserProfile.objects.filter(telegram_id__isnull=False)
        free = sum(1 for p in all_qs if access_tier_label(p) == 'free')
        trial = sum(1 for p in all_qs if access_tier_label(p) == 'trial')
        paid = sum(1 for p in all_qs if has_active_subscription(p))
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Total users: {all_qs.count()} · free: {free} · trial: {trial} · paid: {paid}',
            ),
        )
        self.stdout.write(
            'Payments: /admin/billing_app/payment/ · '
            'SSH: python manage.py list_user_billing --tier paid',
        )
