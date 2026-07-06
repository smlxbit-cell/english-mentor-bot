"""Sync media/spirit/ folder → CharacterMedia (auto keys from filenames).

Folder layout:
  media/spirit/emotions/greeting.mp4  → full clip (lessons)
  media/spirit/notes/greeting.mp4     → optional manual square for /start circle
  media/spirit/scenes/ep01_cafe.jpg

Upload messages are deleted from chat after registering file_id.

Example:
  python manage.py sync_spirit_media --force
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telegram import Bot
from telegram.error import BadRequest, TimedOut
from telegram.request import HTTPXRequest

from config.settings import TELEGRAM_BOT_TOKEN
from content_app.models import Character, CharacterMedia
from telegram_app.bot.mentor import EMOTION_KEYS
from telegram_app.spirit_video import ffmpeg_path, make_square_note, needs_square_crop

SPIRIT_ROOT = Path('media') / 'spirit'
EMOTION_EXTS = {'.mp4', '.gif', '.webm', '.mov'}
SCENE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
# Circle diameter on screen (pixels). 200 = small, like other bots.
VIDEO_NOTE_LENGTH = 200


def _kind_for_path(path: Path, *, is_scene: bool) -> str:
    if path.suffix.lower() in SCENE_EXTS:
        return CharacterMedia.MediaKind.IMAGE
    if path.suffix.lower() in EMOTION_EXTS:
        return CharacterMedia.MediaKind.ANIMATION
    return CharacterMedia.MediaKind.ANIMATION


class Command(BaseCommand):
    help = 'Scan media/spirit and register all clips by filename.'

    def add_arguments(self, parser):
        parser.add_argument('--character', default='Spirit')
        parser.add_argument(
            '--chat-id', type=int, default=None,
            help='Your personal Telegram user ID (optional if you already used the bot)',
        )
        parser.add_argument(
            '--missing-only', action='store_true',
            help='Skip files that already have telegram_file_id',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Re-upload all files (after you replace a video)',
        )
        parser.add_argument(
            '--notes-only', action='store_true',
            help='Only register compact circles (for /start welcome).',
        )

    def handle(self, *args, **options):
        if not TELEGRAM_BOT_TOKEN:
            raise CommandError('TELEGRAM_BOT_TOKEN is not set.')

        chat_id = options['chat_id'] or self._resolve_chat_id()
        if not chat_id:
            raise CommandError(
                'Could not find your Telegram ID.\n'
                '1) Open the bot in Telegram and send /start\n'
                '2) Run: python manage.py list_telegram_users\n'
                '3) Run: python manage.py sync_spirit_media --chat-id YOUR_NUMBER'
            )
        self.stdout.write(f'Upload target chat_id: {chat_id} (messages deleted after sync)')

        root = Path(settings.BASE_DIR) / SPIRIT_ROOT
        if not root.is_dir():
            raise CommandError(f'Folder not found: {root}')

        char, _ = Character.objects.get_or_create(
            name=options['character'],
            defaults={
                'role': 'языковой дух — спутник ученика',
                'personality': 'warm, playful, encouraging',
                'speaking_style': 'short, friendly, simple English',
            },
        )

        uploaded = 0
        skipped = 0
        if not options['notes_only']:
            files = self._collect_files(root)
            if not files:
                self.stderr.write(f'No media files under {root}')
            else:
                for key, path, is_scene in files:
                    existing = CharacterMedia.objects.filter(character=char, key=key).first()
                    if options['missing_only'] and existing and existing.telegram_file_id:
                        skipped += 1
                        continue
                    if not options['force'] and existing and existing.telegram_file_id:
                        rel = str(path.relative_to(root)).replace('\\', '/')
                        if existing.source_path == rel:
                            skipped += 1
                            continue

                    kind = _kind_for_path(path, is_scene=is_scene)
                    rel_path = str(path.relative_to(root)).replace('\\', '/')
                    try:
                        file_id, media_kind = asyncio.run(
                            self._upload(path, chat_id, kind),
                        )
                    except BadRequest as exc:
                        if 'chat not found' in str(exc).lower():
                            raise CommandError(
                                f'Chat not found for id {chat_id}.\n'
                                'Run: python manage.py list_telegram_users'
                            ) from exc
                        raise CommandError(f'Telegram rejected {path.name}: {exc}') from exc
                    except TimedOut as exc:
                        raise CommandError(
                            f'Upload timed out ({path.name}). Check internet / VPN.',
                        ) from exc
                    CharacterMedia.objects.update_or_create(
                        character=char,
                        key=key,
                        defaults={
                            'kind': media_kind,
                            'title': key.replace('_', ' '),
                            'telegram_file_id': file_id,
                            'source_path': rel_path,
                        },
                    )
                    uploaded += 1
                    self.stdout.write(f'  OK {key} <- {rel_path}')

        notes_uploaded = self._sync_video_notes(char, root, chat_id, options)

        self.stdout.write(self.style.SUCCESS(
            f'Done: {uploaded} full, {skipped} skipped, {notes_uploaded} circles.',
        ))
        if notes_uploaded == 0 and not ffmpeg_path():
            self.stdout.write(self.style.WARNING(
                'Install ffmpeg for auto square crop, or add media/spirit/notes/greeting.mp4 (1:1).',
            ))

    def _collect_files(self, root: Path) -> list[tuple[str, Path, bool]]:
        items: list[tuple[str, Path, bool]] = []
        emotions_dir = root / 'emotions'
        scenes_dir = root / 'scenes'

        if emotions_dir.is_dir():
            for path in sorted(emotions_dir.iterdir()):
                if path.is_file() and path.suffix.lower() in EMOTION_EXTS | SCENE_EXTS:
                    items.append((path.stem.lower(), path, False))

        if scenes_dir.is_dir():
            for path in sorted(scenes_dir.iterdir()):
                if path.is_file() and path.suffix.lower() in SCENE_EXTS:
                    items.append((path.stem.lower(), path, True))

        for path in sorted(root.iterdir()):
            if path.is_file() and path.suffix.lower() in EMOTION_EXTS:
                key = path.stem.lower()
                if not any(k == key for k, _, _ in items):
                    items.append((key, path, False))

        return items

    def _sync_video_notes(
        self,
        char: Character,
        root: Path,
        chat_id: int,
        options: dict,
    ) -> int:
        notes_dir = root / 'notes'
        emotions_dir = root / 'emotions'
        candidates: dict[str, Path] = {}

        if notes_dir.is_dir():
            for path in sorted(notes_dir.iterdir()):
                if path.is_file() and path.suffix.lower() in EMOTION_EXTS:
                    if path.stem.endswith('.square'):
                        continue
                    candidates[path.stem.lower()] = path

        if emotions_dir.is_dir():
            for path in sorted(emotions_dir.iterdir()):
                if path.is_file() and path.suffix.lower() in EMOTION_EXTS:
                    key = path.stem.lower()
                    candidates.setdefault(key, path)

        if not candidates:
            self.stdout.write('No emotion clips found for video notes.')
            return 0

        uploaded = 0
        for key, path in sorted(candidates.items()):
            rel_path = str(path.relative_to(root)).replace('\\', '/')
            existing = CharacterMedia.objects.filter(character=char, key=key).first()
            if (
                not options['force']
                and existing
                and existing.telegram_video_note_id
                and existing.note_source_path == rel_path
            ):
                continue

            upload_path = path
            if path.parent.name != 'notes' or needs_square_crop(path, root):
                square = make_square_note(path, root)
                if square:
                    upload_path = square
                    self.stdout.write(f'  crop {key} -> {upload_path.name}')
                elif path.parent.name == 'emotions':
                    self.stdout.write(self.style.WARNING(
                        f'  skip note {key}: need ffmpeg or notes/{key}.mp4 (square)',
                    ))
                    continue

            try:
                note_id = asyncio.run(self._upload_video_note(upload_path, chat_id))
            except BadRequest as exc:
                self.stdout.write(self.style.WARNING(f'  skip note {key}: {exc}'))
                continue
            except TimedOut as exc:
                raise CommandError(f'Video note timed out ({path.name}).') from exc

            clip, _ = CharacterMedia.objects.get_or_create(
                character=char,
                key=key,
                defaults={'title': key.replace('_', ' ')},
            )
            clip.telegram_video_note_id = note_id
            clip.note_source_path = rel_path
            clip.save(update_fields=['telegram_video_note_id', 'note_source_path'])
            uploaded += 1
            self.stdout.write(f'  OK circle {key}')

        return uploaded

    def _resolve_chat_id(self) -> int | None:
        from users_app.models import UserProfile

        profile = (
            UserProfile.objects.filter(telegram_id__isnull=False)
            .order_by('-last_seen', '-id')
            .first()
        )
        return int(profile.telegram_id) if profile else None

    def _bot(self) -> Bot:
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=120.0,
            write_timeout=120.0,
        )
        return Bot(token=TELEGRAM_BOT_TOKEN, request=request)

    async def _delete_upload(self, bot: Bot, chat_id: int, message_id: int) -> None:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass

    async def _upload(self, path: Path, chat_id: int, kind: str) -> tuple[str, str]:
        bot = self._bot()
        size_kb = path.stat().st_size // 1024
        self.stdout.write(f'  ^ upload {path.name} ({size_kb} KB)...')
        with path.open('rb') as fh:
            if kind == CharacterMedia.MediaKind.IMAGE:
                msg = await bot.send_photo(chat_id=chat_id, photo=fh)
                file_id = msg.photo[-1].file_id
            else:
                media_kind = kind
                try:
                    msg = await bot.send_animation(chat_id=chat_id, animation=fh)
                except BadRequest:
                    fh.seek(0)
                    msg = await bot.send_video(chat_id=chat_id, video=fh)
                    media_kind = CharacterMedia.MediaKind.ANIMATION
                fid = msg.animation or msg.video
                if not fid:
                    raise BadRequest(f'Telegram rejected: {path.name}')
                file_id = fid.file_id
                kind = media_kind
        await self._delete_upload(bot, chat_id, msg.message_id)
        return file_id, kind

    async def _upload_video_note(self, path: Path, chat_id: int) -> str:
        bot = self._bot()
        size_kb = path.stat().st_size // 1024
        self.stdout.write(
            f'  ^ circle {path.name} ({size_kb} KB, {VIDEO_NOTE_LENGTH}px)...',
        )
        with path.open('rb') as fh:
            msg = await bot.send_video_note(
                chat_id=chat_id,
                video_note=fh,
                length=VIDEO_NOTE_LENGTH,
            )
        if not msg.video_note:
            raise BadRequest(f'Telegram rejected video note: {path.name}')
        file_id = msg.video_note.file_id
        await self._delete_upload(bot, chat_id, msg.message_id)
        return file_id
