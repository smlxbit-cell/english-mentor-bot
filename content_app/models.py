from django.db import models


class ContentTheme(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Phrase(models.Model):
    class CefrLevel(models.TextChoices):
        A1 = 'A1', 'A1'
        A2 = 'A2', 'A2'
        B1 = 'B1', 'B1'
        B2 = 'B2', 'B2'
        C1 = 'C1', 'C1'

    english_text = models.CharField(max_length=255)
    translation = models.CharField(max_length=255, blank=True)
    explanation = models.TextField(blank=True)

    level = models.CharField(
        max_length=2,
        choices=CefrLevel.choices,
        default=CefrLevel.A1,
    )

    theme = models.ForeignKey(
        ContentTheme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='phrases',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['english_text']

    def __str__(self):
        return self.english_text


class Character(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=150, blank=True)
    personality = models.TextField(blank=True)
    speaking_style = models.CharField(
        max_length=255,
        blank=True,
        help_text='Short hint for AI dialogue tone, e.g. "simple, warm, short sentences".',
    )

    avatar_url = models.URLField(blank=True)
    video_note_file_id = models.CharField(
        max_length=500,
        blank=True,
        help_text='Telegram file_id for circular video (video note) shown during AI dialogue.',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CharacterMedia(models.Model):
    """Reaction / scene clip for a character (GIF, image, video note).

    Upload once via ``register_character_media`` — Telegram ``file_id`` is reused.
    Keys examples: greeting, joy, praise, think, surprise, goodbye, scene_cafe.
    """

    class MediaKind(models.TextChoices):
        ANIMATION = 'animation', 'GIF / short MP4'
        IMAGE = 'image', 'Photo'
        VIDEO_NOTE = 'video_note', 'Circle video'

    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='media_clips',
    )
    key = models.SlugField(max_length=60, help_text='e.g. greeting, joy, scene_cafe')
    kind = models.CharField(max_length=20, choices=MediaKind.choices, default=MediaKind.ANIMATION)
    title = models.CharField(max_length=150, blank=True)
    telegram_file_id = models.CharField(max_length=500, blank=True)
    telegram_video_note_id = models.CharField(
        max_length=500, blank=True,
        help_text='Circular video note file_id (compact, for welcome / menus).',
    )
    source_path = models.CharField(
        max_length=255,
        blank=True,
        help_text='Relative path under media/spirit/ (for sync & replace)',
    )
    note_source_path = models.CharField(
        max_length=255,
        blank=True,
        help_text='Square clip under media/spirit/notes/ for video note.',
    )
    file = models.FileField(upload_to='character_media/', blank=True, null=True)

    class Meta:
        ordering = ['character', 'key']
        unique_together = [('character', 'key')]

    def __str__(self):
        return f'{self.character.name}:{self.key}'


class StoryArc(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class StoryEpisode(models.Model):
    class CefrLevel(models.TextChoices):
        A1 = 'A1', 'A1'
        A2 = 'A2', 'A2'
        B1 = 'B1', 'B1'
        B2 = 'B2', 'B2'
        C1 = 'C1', 'C1'

    arc = models.ForeignKey(
        StoryArc,
        on_delete=models.CASCADE,
        related_name='episodes',
    )

    episode_number = models.PositiveIntegerField()

    title = models.CharField(max_length=150)

    level = models.CharField(
        max_length=2,
        choices=CefrLevel.choices,
        default=CefrLevel.A1,
    )

    theme = models.ForeignKey(
        ContentTheme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='episodes',
    )

    characters = models.ManyToManyField(
        Character,
        blank=True,
        related_name='episodes',
    )

    target_phrases = models.ManyToManyField(
        Phrase,
        blank=True,
        related_name='episodes',
    )

    short_summary = models.TextField(blank=True)
    story_text = models.TextField()

    choices = models.JSONField(default=list, blank=True)
    target_words = models.JSONField(default=list, blank=True)

    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['arc', 'episode_number']
        constraints = [
            models.UniqueConstraint(
                fields=['arc', 'episode_number'],
                name='unique_episode_in_arc',
            )
        ]

    def __str__(self):
        return f'{self.arc.title} — Episode {self.episode_number}: {self.title}'


class MediaAsset(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = 'image', 'Image'
        AUDIO = 'audio', 'Audio'
        VIDEO = 'video', 'Video'
        VIDEO_NOTE = 'video_note', 'Video note (circle)'
        GIF = 'gif', 'GIF / animation'

    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
    )

    title = models.CharField(max_length=150)
    file = models.FileField(upload_to='media_assets/', blank=True, null=True)
    source_url = models.URLField(blank=True)

    license_name = models.CharField(max_length=100, blank=True)
    author = models.CharField(max_length=150, blank=True)

    telegram_file_id = models.CharField(
        max_length=500,
        blank=True,
        help_text='Cached Telegram file_id to re-send media without re-uploading.',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.media_type}: {self.title}'


# ============================================================
# Interactive lessons + adaptive diagnostic (authored content)
# ============================================================

LEVEL_CHOICES = [
    ('a1', 'A1'),
    ('a2', 'A2'),
    ('b1', 'B1'),
    ('b2', 'B2'),
]

SKILL_CHOICES = [
    ('grammar', 'Grammar'),
    ('vocabulary', 'Vocabulary'),
    ('reading', 'Reading'),
    ('listening', 'Listening'),
    ('speaking', 'Speaking'),
    ('writing', 'Writing'),
    ('pronunciation', 'Pronunciation'),
    ('mixed', 'Mixed'),
]


class DiagnosticItem(models.Model):
    """One adaptive diagnostic question. Checked deterministically (0 tokens)."""

    class ItemType(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', 'Multiple choice'
        FILL_GAP = 'fill_gap', 'Fill the gap'
        TRANSLATION = 'translation_ru_en', 'Translation RU → EN'
        LISTENING = 'listening', 'Listening (audio → choice)'
        SPEAKING = 'speaking', 'Speaking (voice)'

    level = models.CharField(max_length=5, choices=LEVEL_CHOICES)
    skill = models.CharField(max_length=20, choices=SKILL_CHOICES, default='grammar')
    item_type = models.CharField(max_length=30, choices=ItemType.choices)

    prompt = models.TextField(help_text='Question text (may be in Russian).')

    options = models.JSONField(
        default=list, blank=True,
        help_text="Answer options for choice types, e.g. ['drink', 'drinks', 'drinking'].",
    )
    correct = models.JSONField(
        default=list, blank=True,
        help_text="Accepted answers, e.g. ['drinks'] or ['i was at home yesterday'].",
    )
    keywords = models.JSONField(
        default=list, blank=True,
        help_text='Must-have keywords for translation/speaking checks.',
    )
    explanation_ru = models.TextField(
        blank=True,
        help_text='Short tip shown when the learner answers wrong.',
    )

    audio = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='diagnostic_items',
        help_text='Audio for listening / target phrase for speaking items.',
    )

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['level', 'order', 'id']

    def __str__(self):
        return f'[{self.level.upper()}/{self.skill}] {self.prompt[:50]}'


class Unit(models.Model):
    """A curriculum module: an ordered group of lessons within a level."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=160, unique=True)
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='a1')
    description = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level', 'order', 'id']

    def __str__(self):
        return f'[{self.level.upper()}] {self.title}'


class Lesson(models.Model):
    """A single interactive lesson = an ordered sequence of LessonStep."""

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='a1')

    unit = models.ForeignKey(
        'Unit', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lessons',
    )

    theme = models.ForeignKey(
        ContentTheme, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lessons',
    )
    story_episode = models.ForeignKey(
        StoryEpisode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lessons',
    )
    character = models.ForeignKey(
        Character, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lessons',
    )
    cover = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lesson_covers',
    )

    intro_text = models.TextField(blank=True)
    outro_text = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)
    is_trial = models.BooleanField(default=False, help_text='Available for free (trial).')
    is_published = models.BooleanField(default=False)

    estimated_minutes = models.PositiveIntegerField(default=8)
    xp_reward = models.PositiveIntegerField(default=50)

    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'order', 'id']

    def __str__(self):
        flag = 'trial' if self.is_trial else 'paid'
        return f'[{self.level.upper()}/{flag}] {self.title}'


class LessonStep(models.Model):
    """One step in a lesson.

    Content steps just display something. Interactive steps (exercise / speaking
    / dialogue / ai_dialogue) carry their parameters in `content` (JSON) and are
    checked by ai_app.services. This keeps the whole lesson as one ordered list.
    """

    class StepType(models.TextChoices):
        HOOK = 'hook', 'Hook'
        STORY = 'story', 'Story scene'
        IMAGE = 'image', 'Image'
        GIF = 'gif', 'GIF'
        AUDIO = 'audio', 'Audio'
        VIDEO = 'video', 'Video'
        VOCABULARY = 'vocabulary', 'Vocabulary cards'
        GRAMMAR_NOTE = 'grammar_note', 'Grammar note'
        DIALOGUE = 'dialogue', 'Scripted dialogue'
        EXERCISE = 'exercise', 'Exercise'
        SPEAKING = 'speaking', 'Speaking (voice)'
        AI_DIALOGUE = 'ai_dialogue', 'Free AI dialogue'
        REFLECTION = 'reflection', 'Reflection'
        REWARD = 'reward', 'Reward'
        CLIFFHANGER = 'cliffhanger', 'Cliffhanger'

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name='steps',
    )
    order = models.PositiveIntegerField(default=0)
    step_type = models.CharField(max_length=30, choices=StepType.choices)

    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)

    media = models.ForeignKey(
        MediaAsset, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lesson_steps',
    )
    character = models.ForeignKey(
        Character, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lesson_steps',
    )

    skill = models.CharField(max_length=20, choices=SKILL_CHOICES, default='mixed')

    content = models.JSONField(
        default=dict, blank=True,
        help_text=(
            'Structured data. For interactive steps: '
            "{'exercise_type','options','correct','keywords','hints',"
            "'explanation','ai_fallback','ai_check_prompt','points','target'}."
        ),
    )

    xp_reward = models.PositiveIntegerField(default=10)
    is_optional = models.BooleanField(default=False)

    class Meta:
        ordering = ['lesson', 'order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['lesson', 'order'],
                name='unique_step_order_in_lesson',
            )
        ]

    def __str__(self):
        return f'{self.lesson} / {self.order}. {self.step_type}'

    @property
    def is_interactive(self) -> bool:
        return self.step_type in {
            self.StepType.EXERCISE,
            self.StepType.SPEAKING,
            self.StepType.DIALOGUE,
            self.StepType.AI_DIALOGUE,
        }


class GrammarRule(models.Model):
    """Canonical grammar rule for the Rules Library (map by level/topic)."""

    key = models.SlugField(max_length=80, unique=True)
    topic = models.CharField(max_length=100, help_text='Topic group, e.g. «Просьбы».')
    title = models.CharField(max_length=200)
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='a1')

    summary_ru = models.TextField(blank=True)
    table = models.JSONField(default=dict, blank=True)
    examples = models.JSONField(default=list, blank=True)
    tip_ru = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'topic', 'order', 'id']

    def __str__(self):
        return f'[{self.level.upper()}] {self.title}'
