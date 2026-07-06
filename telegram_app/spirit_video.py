"""Square crop for Telegram video notes (compact Spirit circle)."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

SQUARE_SIZE = 480
MAX_SECONDS = 6


def ffmpeg_path() -> str | None:
    found = shutil.which('ffmpeg')
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def square_note_path(source: Path, root: Path) -> Path:
    """Cached square MP4 under media/spirit/notes/."""
    notes_dir = root / 'notes'
    notes_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir / f'{source.stem}.square.mp4'


def needs_square_crop(source: Path, root: Path) -> bool:
    if source.parent.name == 'notes' and source.stem.endswith('.square'):
        return False
    if source.parent.name == 'notes':
        return False
    cached = square_note_path(source, root)
    if cached.is_file() and cached.stat().st_mtime >= source.stat().st_mtime:
        return False
    return True


def make_square_note(source: Path, root: Path) -> Path | None:
    """Center-crop to 1:1 for Telegram video notes. Returns path or None."""
    if source.parent.name == 'notes':
        return source

    cached = square_note_path(source, root)
    if cached.is_file() and cached.stat().st_mtime >= source.stat().st_mtime:
        return cached

    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        logger.warning('ffmpeg not found — cannot auto-crop %s', source.name)
        return None

    cmd = [
        ffmpeg,
        '-y',
        '-i', str(source),
        '-vf', f'crop=min(iw\\,ih):min(iw\\,ih),scale={SQUARE_SIZE}:{SQUARE_SIZE}',
        '-an',
        '-t', str(MAX_SECONDS),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        str(cached),
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.warning('ffmpeg crop failed for %s: %s', source.name, exc)
        return None

    if cached.is_file() and cached.stat().st_size > 0:
        return cached
    return None
