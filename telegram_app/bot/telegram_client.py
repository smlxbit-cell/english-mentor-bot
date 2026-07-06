"""Shared Telegram Bot client (proxy-aware for Yandex VPS)."""

from __future__ import annotations

from django.conf import settings
from telegram import Bot
from telegram.request import HTTPXRequest


def make_bot(
    *,
    connect_timeout: float = 60.0,
    read_timeout: float = 60.0,
    write_timeout: float = 60.0,
    pool_timeout: float = 60.0,
) -> Bot:
    request = HTTPXRequest(
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        write_timeout=write_timeout,
        pool_timeout=pool_timeout,
    )
    kwargs: dict = {
        'token': settings.TELEGRAM_BOT_TOKEN,
        'request': request,
    }
    if settings.TELEGRAM_PROXY:
        kwargs['proxy'] = settings.TELEGRAM_PROXY
    return Bot(**kwargs)
