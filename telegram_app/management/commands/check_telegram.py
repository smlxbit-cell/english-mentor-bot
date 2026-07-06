"""Test reachability of Telegram API from the server."""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Ping api.telegram.org (run on VPS to debug TimedOut).'

    def handle(self, *args, **options):
        import httpx

        url = 'https://api.telegram.org'
        proxy = settings.TELEGRAM_PROXY or None
        if proxy:
            self.stdout.write(f'Using TELEGRAM_PROXY={proxy}')

        try:
            r = httpx.get(
                url, timeout=30.0, follow_redirects=True, proxy=proxy,
            )
            self.stdout.write(self.style.SUCCESS(
                f'OK: {url} → HTTP {r.status_code}',
            ))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                f'FAIL: cannot reach {url}\n{exc}\n'
                'Set up WARP (deploy/setup_warp.sh) or TELEGRAM_PROXY — '
                'see docs/TELEGRAM_PROXY_YANDEX.md',
            ))
