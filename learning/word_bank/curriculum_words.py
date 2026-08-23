"""Extract vocabulary rows from curriculum lesson steps."""

from __future__ import annotations

from content_app.curriculum import CURRICULUM

from .normalize import word_slug


def iter_curriculum_rows() -> list[dict]:
    rows: dict[str, dict] = {}
    for block in CURRICULUM:
        unit_level = (block.get('unit') or {}).get('level') or 'a1'
        for lesson in block.get('lessons') or []:
            level = unit_level
            for step in lesson.get('steps') or []:
                if step.get('type') != 'vocabulary':
                    continue
                words = (step.get('content') or {}).get('words') or []
                tags = lesson.get('tags') or []
                for item in words:
                    if not isinstance(item, dict):
                        continue
                    english = (item.get('en') or item.get('english') or '').strip()
                    translation = (item.get('ru') or item.get('translation') or '').strip()
                    if not english or not translation:
                        continue
                    slug = word_slug(english)
                    rows[slug] = {
                        'slug': slug,
                        'english': english,
                        'translation': translation,
                        'example': (item.get('example') or item.get('example_en') or '').strip(),
                        'example_ru': (item.get('example_ru') or '').strip(),
                        'cefr_level': level,
                        'part_of_speech': (item.get('part_of_speech') or item.get('pos') or '').strip(),
                        'topics': tags,
                    }
    return list(rows.values())
