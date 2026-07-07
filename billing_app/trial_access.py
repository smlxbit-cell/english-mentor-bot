"""Two-day full-app trial (not just two isolated lessons)."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from billing_app.models import Subscription
from users_app.models import UserProfile


def trial_days() -> int:
    return int(getattr(settings, 'TRIAL_DAYS', 2))


def has_active_subscription(profile: UserProfile) -> bool:
    return Subscription.objects.filter(
        user=profile,
        status=Subscription.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    ).exists()


def ensure_trial_started(profile: UserProfile) -> None:
    if not profile.trial_started_at:
        profile.trial_started_at = timezone.now()
        profile.save(update_fields=['trial_started_at', 'updated_at'])


def is_full_trial_active(profile: UserProfile) -> bool:
    if has_active_subscription(profile):
        return False
    ensure_trial_started(profile)
    if not profile.trial_started_at:
        return True
    end = profile.trial_started_at + timedelta(days=trial_days())
    return timezone.now() < end


def has_premium_access(profile: UserProfile) -> bool:
    return has_active_subscription(profile) or is_full_trial_active(profile)


def trial_days_remaining(profile: UserProfile) -> int:
    if not profile.trial_started_at or has_active_subscription(profile):
        return 0
    end = profile.trial_started_at + timedelta(days=trial_days())
    delta = end - timezone.now()
    return max(0, delta.days + (1 if delta.seconds else 0))
