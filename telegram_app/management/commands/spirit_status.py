"""Check which Spirit clips are registered in the database."""

from django.core.management.base import BaseCommand

from content_app.models import Character, CharacterMedia
from telegram_app.bot.mentor import EMOTION_KEYS


class Command(BaseCommand):
    help = 'Show Spirit media keys and whether telegram_file_id is set.'

    def add_arguments(self, parser):
        parser.add_argument('--character', default='Spirit')

    def handle(self, *args, **options):
        char = Character.objects.filter(name__iexact=options['character']).first()
        if not char:
            self.stdout.write(self.style.WARNING(
                f'Character "{options["character"]}" not found. Run: python manage.py seed_content',
            ))
            return

        clips = {
            c.key: c for c in CharacterMedia.objects.filter(character=char)
        }
        ok = 0
        for key in EMOTION_KEYS:
            clip = clips.get(key)
            has_full = bool(clip and clip.telegram_file_id)
            has_note = bool(clip and clip.telegram_video_note_id)
            if has_full and has_note:
                self.stdout.write(self.style.SUCCESS(f'  OK  {key}  (full + circle)'))
                ok += 1
            elif has_full:
                self.stdout.write(self.style.WARNING(f'  ..  {key}  (full only, no circle)'))
            elif has_note:
                self.stdout.write(self.style.SUCCESS(f'  OK  {key}  (circle only)'))
                ok += 1
            else:
                self.stdout.write(self.style.ERROR(f'  --  {key}  (missing)'))

        scenes = [k for k in clips if k not in EMOTION_KEYS]
        for key in sorted(scenes):
            clip = clips[key]
            mark = 'OK' if clip.telegram_file_id else '--'
            self.stdout.write(f'  {mark}  {key} (scene)')

        greeting = clips.get('greeting')
        if greeting and greeting.telegram_video_note_id:
            self.stdout.write(self.style.SUCCESS(
                '\n/start welcome circle: READY',
            ))
        elif greeting and greeting.telegram_file_id:
            self.stdout.write(self.style.WARNING(
                '\n/start circle: run sync_spirit_media --notes-only --force',
            ))

        sleep = clips.get('sleep')
        if sleep and sleep.telegram_video_note_id:
            self.stdout.write('long absence (sleep): READY')
        elif 'sleep' in EMOTION_KEYS:
            self.stdout.write(self.style.WARNING(
                'long absence (sleep): add media/spirit/emotions/sleep.mp4',
            ))

        self.stdout.write(
            '\nFull map: docs/SPIRIT_EMOTIONS.md',
        )
