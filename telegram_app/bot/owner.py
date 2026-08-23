"""Bot owner alerts and /owner dashboard (no SSH required)."""

from __future__ import annotations

import logging

from django.conf import settings
from telegram.ext import ContextTypes

from billing_app.owner_dashboard import (
    new_user_alert_text,
    owner_dashboard_text,
    payment_alert_text,
)

logger = logging.getLogger(__name__)


def bot_owner_telegram_ids() -> frozenset[int]:
    raw = getattr(settings, 'BOT_OWNER_TELEGRAM_IDS', '') or ''
    ids: set[int] = set()
    for part in raw.replace(';', ',').split(','):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return frozenset(ids)


def is_bot_owner(telegram_id: int | None) -> bool:
    if telegram_id is None:
        return False
    owners = bot_owner_telegram_ids()
    return bool(owners) and telegram_id in owners


async def notify_bot_owners(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    for owner_id in bot_owner_telegram_ids():
        try:
            await context.bot.send_message(
                chat_id=owner_id,
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True,
            )
        except Exception:
            logger.exception('Failed to notify owner %s', owner_id)


async def notify_new_user(context: ContextTypes.DEFAULT_TYPE, profile: dict) -> None:
    if not profile.get('just_created'):
        return
    from users_app.models import UserProfile

    try:
        user = UserProfile.objects.get(id=profile['id'])
    except UserProfile.DoesNotExist:
        return
    await notify_bot_owners(context, new_user_alert_text(user))


async def notify_payment(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    user_name: str,
    plan_code: str,
    amount_rub: int,
) -> None:
    await notify_bot_owners(
        context,
        payment_alert_text(user_name=user_name, plan_code=plan_code, amount_rub=amount_rub),
    )
