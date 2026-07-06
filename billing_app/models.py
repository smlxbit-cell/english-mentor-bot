from datetime import timedelta

from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """A tariff plan. For the prototype there is a single active plan (390 RUB)."""

    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    price_rub = models.PositiveIntegerField(default=390)
    duration_days = models.PositiveIntegerField(default=30)

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price_rub']

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
