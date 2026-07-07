from datetime import timedelta

from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """A tariff plan (subscription or voice add-on)."""

    class PlanKind(models.TextChoices):
        SUBSCRIPTION = 'subscription', 'Subscription'
        VOICE_ADDON = 'voice_addon', 'Voice add-on'

    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    price_rub = models.PositiveIntegerField(default=590)
    duration_days = models.PositiveIntegerField(default=30)

    plan_kind = models.CharField(
        max_length=20,
        choices=PlanKind.choices,
        default=PlanKind.SUBSCRIPTION,
    )
    voice_minutes_monthly = models.PositiveIntegerField(
        default=60,
        help_text='Included voice minutes per billing month (subscription plans).',
    )
    voice_minutes_in_pack = models.PositiveIntegerField(
        default=0,
        help_text='Minutes granted on purchase (voice add-on packs).',
    )
    tutor_ai_daily_limit = models.PositiveIntegerField(
        default=80,
        help_text='Soft anti-spam cap per calendar day (not the main tutor budget).',
    )
    tutor_ai_monthly_limit = models.PositiveIntegerField(
        default=500,
        help_text='Tutor AI replies included per calendar month (main budget).',
    )
    stt_model = models.CharField(
        max_length=80,
        blank=True,
        help_text='AITUNNEL STT model slug for mentor voice, e.g. whisper-large-v3-turbo.',
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'price_rub']

    def __str__(self):
        return f'{self.name} — {self.price_rub} ₽ / {self.duration_days} дней'

    @property
    def price_kopeks(self) -> int:
        return self.price_rub * 100


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expires_at']

    def __str__(self):
        return f'{self.user} — {self.plan} — {self.status}'

    @property
    def is_currently_active(self) -> bool:
        return self.status == self.Status.ACTIVE and self.expires_at > timezone.now()

    @classmethod
    def activate(cls, user, plan, *, from_now=True):
        """Create/extend an active subscription. Stacks on top of an active one."""
        now = timezone.now()
        current = (
            cls.objects.filter(user=user, status=cls.Status.ACTIVE, expires_at__gt=now)
            .order_by('-expires_at')
            .first()
        )
        start = current.expires_at if (current and not from_now) else now
        if current:
            start = current.expires_at
        return cls.objects.create(
            user=user,
            plan=plan,
            status=cls.Status.ACTIVE,
            started_at=start,
            expires_at=start + timedelta(days=plan.duration_days),
        )


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='payments',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
    )

    provider = models.CharField(max_length=100, default='mock')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    amount_rub = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=10, default='RUB')

    payload = models.CharField(max_length=255, blank=True)
    provider_payment_id = models.CharField(max_length=255, blank=True)

    raw_data = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.amount_rub} ₽ — {self.status}'
