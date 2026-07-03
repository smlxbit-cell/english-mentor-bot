from django.db import models
from django.utils import timezone


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username or self.first_name or str(self.telegram_id)


class UserProfile(models.Model):
    LEVEL_CHOICES = [
        ('unknown', 'Unknown'),
        ('a1', 'A1'),
        ('a2', 'A2'),
        ('b1', 'B1'),
        ('b2', 'B2'),
    ]

    user = models.OneToOneField(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='unknown'
    )

    diagnostic_completed = models.BooleanField(default=False)
    trial_lessons_used = models.PositiveIntegerField(default=0)
    trial_lessons_limit = models.PositiveIntegerField(default=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def has_trial_access(self):
        return self.trial_lessons_used < self.trial_lessons_limit

    def __str__(self):
        return f'{self.user} — {self.level}'


class DiagnosticQuestion(models.Model):
    LEVEL_CHOICES = [
        ('a1', 'A1'),
        ('a2', 'A2'),
        ('b1', 'B1'),
        ('b2', 'B2'),
    ]

    text = models.TextField()
    correct_answer = models.CharField(max_length=500)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.level.upper()} — {self.text[:50]}'


class DiagnosticAnswer(models.Model):
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='diagnostic_answers'
    )
    question = models.ForeignKey(
        DiagnosticQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    user_answer = models.TextField()
    is_correct = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} — {self.question}'


class SubscriptionPlan(models.Model):
    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='RUB')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} — {self.price} {self.currency}'


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_active(self):
        return self.status == 'active' and self.expires_at > timezone.now()

    def __str__(self):
        return f'{self.user} — {self.plan} — {self.status}'


class Lesson(models.Model):
    LEVEL_CHOICES = [
        ('a1', 'A1'),
        ('a2', 'A2'),
        ('b1', 'B1'),
        ('b2', 'B2'),
    ]

    title = models.CharField(max_length=255)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)

    is_trial = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.level.upper()} — {self.title}'


class UserLessonProgress(models.Model):
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='lesson_progress'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )

    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f'{self.user} — {self.lesson}'


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    provider = models.CharField(max_length=100, default='telegram_yookassa')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='RUB')

    payload = models.CharField(max_length=255)

    telegram_payment_charge_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    provider_payment_charge_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    raw_data = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} — {self.amount} {self.currency} — {self.status}'


# ============================================================
# New adaptive content architecture
# ============================================================

STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('review', 'Review'),
    ('published', 'Published'),
    ('archived', 'Archived'),
]

CEFR_LEVEL_CHOICES = [
    ('pre_a1', 'Pre-A1'),
    ('a1', 'A1'),
    ('a2', 'A2'),
    ('b1', 'B1'),
    ('b2', 'B2'),
    ('c1', 'C1'),
    ('c2', 'C2'),
]

DIFFICULTY_CHOICES = [
    ('very_easy', 'Very easy'),
    ('easy', 'Easy'),
    ('normal', 'Normal'),
    ('hard', 'Hard'),
    ('very_hard', 'Very hard'),
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

MEDIA_TYPE_CHOICES = [
    ('image', 'Image'),
    ('audio', 'Audio'),
    ('video', 'Video'),
    ('document', 'Document'),
    ('pdf', 'PDF'),
    ('external_link', 'External link'),
]

LESSON_BLOCK_TYPE_CHOICES = [
    ('hook', 'Hook / engaging start'),
    ('motivation', 'Motivation'),
    ('story_scene', 'Story scene'),
    ('image', 'Image'),
    ('audio_dialogue', 'Audio dialogue'),
    ('video', 'Video'),
    ('theory', 'Theory'),
    ('grammar_note', 'Grammar note'),
    ('vocabulary', 'Vocabulary'),
    ('phrase_bank', 'Phrase bank'),
    ('example', 'Example'),
    ('dialogue', 'Dialogue'),
    ('mini_quiz', 'Mini quiz'),
    ('exercise_group', 'Exercise group'),
    ('speaking_prompt', 'Speaking prompt'),
    ('writing_prompt', 'Writing prompt'),
    ('reflection', 'Reflection'),
    ('cliffhanger', 'Cliffhanger'),
    ('homework', 'Homework'),
    ('review', 'Review'),
]

EXERCISE_TYPE_CHOICES = [
    ('multiple_choice', 'Multiple choice'),
    ('fill_gap', 'Fill the gap'),
    ('translation_ru_en', 'Translation RU → EN'),
    ('translation_en_ru', 'Translation EN → RU'),
    ('word_order', 'Word order'),
    ('matching', 'Matching'),
    ('true_false', 'True / False'),
    ('short_answer', 'Short answer'),
    ('writing', 'Writing'),
    ('speaking_prompt', 'Speaking prompt'),
    ('listening_comprehension', 'Listening comprehension'),
    ('dialogue_simulation', 'Dialogue simulation'),
    ('error_correction', 'Error correction'),
    ('vocabulary_card', 'Vocabulary card'),
]

CHECKING_TYPE_CHOICES = [
    ('auto_exact', 'Auto: exact answer'),
    ('auto_options', 'Auto: options'),
    ('auto_keywords', 'Auto: keywords'),
    ('ai', 'AI checked'),
    ('manual', 'Manual'),
]


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')

    class Meta:
        abstract = True


class Level(TimeStampedModel):
    code = models.CharField(
        max_length=20,
        choices=CEFR_LEVEL_CHOICES,
        unique=True,
        verbose_name='Level code',
    )
    title = models.CharField(max_length=100, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')
    order = models.PositiveIntegerField(default=0, verbose_name='Order')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        ordering = ['order', 'code']
        verbose_name = 'Level'
        verbose_name_plural = 'Levels'

    def __str__(self):
        return self.title or self.code.upper()


class Course(TimeStampedModel):
    title = models.CharField(max_length=255, verbose_name='Title')
    subtitle = models.CharField(max_length=255, blank=True, verbose_name='Subtitle')
    description = models.TextField(blank=True, verbose_name='Description')

    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Main level',
    )

    goal = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Main learning goal',
        help_text='Например: travel, work, relocation, general English',
    )

    cover_image = models.ForeignKey(
        'MediaAsset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_covers',
        verbose_name='Cover image',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return self.title


class CourseModule(TimeStampedModel):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Course',
    )
    title = models.CharField(max_length=255, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')

    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modules',
        verbose_name='Level',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')

    class Meta:
        ordering = ['course', 'order', 'title']
        verbose_name = 'Course module'
        verbose_name_plural = 'Course modules'

    def __str__(self):
        return f'{self.course} / {self.title}'


class Topic(TimeStampedModel):
    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name='Module',
    )

    title = models.CharField(max_length=255, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')

    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='topics',
        verbose_name='Level',
    )

    primary_skill = models.CharField(
        max_length=30,
        choices=SKILL_CHOICES,
        default='mixed',
        verbose_name='Primary skill',
    )

    grammar_focus = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Grammar focus',
        help_text="Например: ['present_simple', 'word_order']",
    )
    vocabulary_focus = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Vocabulary focus',
        help_text="Например: ['coffee_shop', 'travel_phrases']",
    )

    communication_goal = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Communication goal',
        help_text='Например: заказать кофе, спросить дорогу, рассказать о себе',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')

    class Meta:
        ordering = ['module', 'order', 'title']
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'

    def __str__(self):
        return f'{self.module} / {self.title}'


class MediaAsset(TimeStampedModel):
    title = models.CharField(max_length=255, verbose_name='Title')
    media_type = models.CharField(
        max_length=30,
        choices=MEDIA_TYPE_CHOICES,
        verbose_name='Media type',
    )

    file = models.FileField(
        upload_to='lesson_media/',
        null=True,
        blank=True,
        verbose_name='File',
    )

    external_url = models.URLField(
        blank=True,
        verbose_name='External URL',
        help_text='Если файл хранится не у нас, а по ссылке.',
    )

    telegram_file_id = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Telegram file_id',
        help_text='Сохраняем после первой отправки в Telegram, чтобы потом отправлять быстрее.',
    )

    thumbnail = models.ImageField(
        upload_to='lesson_media/thumbnails/',
        null=True,
        blank=True,
        verbose_name='Thumbnail',
    )

    caption = models.TextField(blank=True, verbose_name='Caption')
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Alt text')

    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Duration seconds',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media asset'
        verbose_name_plural = 'Media assets'

    def __str__(self):
        return f'{self.title} ({self.media_type})'


class StoryWorld(TimeStampedModel):
    title = models.CharField(max_length=255, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')

    target_level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='story_worlds',
        verbose_name='Target level',
    )

    main_goal = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Main goal',
        help_text='Например: travel, work, relocation, daily communication',
    )

    cover_image = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='story_world_covers',
        verbose_name='Cover image',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')

    class Meta:
        ordering = ['title']
        verbose_name = 'Story world'
        verbose_name_plural = 'Story worlds'

    def __str__(self):
        return self.title


class StorySeason(TimeStampedModel):
    story_world = models.ForeignKey(
        StoryWorld,
        on_delete=models.CASCADE,
        related_name='seasons',
        verbose_name='Story world',
    )

    title = models.CharField(max_length=255, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')

    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='story_seasons',
        verbose_name='Level',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')

    cover_image = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='story_season_covers',
        verbose_name='Cover image',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        ordering = ['story_world', 'order', 'title']
        verbose_name = 'Story season'
        verbose_name_plural = 'Story seasons'

    def __str__(self):
        return f'{self.story_world} / {self.title}'


class StoryCharacter(TimeStampedModel):
    story_world = models.ForeignKey(
        StoryWorld,
        on_delete=models.CASCADE,
        related_name='characters',
        verbose_name='Story world',
    )

    name = models.CharField(max_length=100, verbose_name='Name')
    role = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Role',
        help_text='Например: main character, friend, colleague, barista',
    )

    description = models.TextField(blank=True, verbose_name='Description')
    personality = models.TextField(
        blank=True,
        verbose_name='Personality',
        help_text='Характер персонажа: shy, funny, strict, friendly etc.',
    )
    speaking_style = models.TextField(
        blank=True,
        verbose_name='Speaking style',
        help_text='Как говорит персонаж: short phrases, polite, informal etc.',
    )

    avatar = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='character_avatars',
        verbose_name='Avatar',
    )

    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        ordering = ['story_world', 'name']
        verbose_name = 'Story character'
        verbose_name_plural = 'Story characters'

    def __str__(self):
        return f'{self.name} ({self.story_world})'


class StoryEpisode(TimeStampedModel):
    season = models.ForeignKey(
        StorySeason,
        on_delete=models.CASCADE,
        related_name='episodes',
        verbose_name='Season',
    )

    title = models.CharField(max_length=255, verbose_name='Title')
    summary = models.TextField(blank=True, verbose_name='Summary')

    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='story_episodes',
        verbose_name='Level',
    )

    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='story_episodes',
        verbose_name='Related topic',
    )

    grammar_focus = models.JSONField(default=list, blank=True, verbose_name='Grammar focus')
    vocabulary_focus = models.JSONField(default=list, blank=True, verbose_name='Vocabulary focus')

    communication_goal = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Communication goal',
    )

    main_image = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='episode_main_images',
        verbose_name='Main image',
    )

    trailer_video = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='episode_trailers',
        verbose_name='Trailer video',
    )

    cliffhanger = models.TextField(
        blank=True,
        verbose_name='Cliffhanger',
        help_text='Интригующий финал серии.',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')

    class Meta:
        ordering = ['season', 'order', 'title']
        verbose_name = 'Story episode'
        verbose_name_plural = 'Story episodes'

    def __str__(self):
        return f'{self.season} / Episode {self.order}: {self.title}'


class StoryScene(TimeStampedModel):
    episode = models.ForeignKey(
        StoryEpisode,
        on_delete=models.CASCADE,
        related_name='scenes',
        verbose_name='Episode',
    )

    title = models.CharField(max_length=255, verbose_name='Title')
    text = models.TextField(blank=True, verbose_name='Narrative text')

    dialogue = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Dialogue',
        help_text=(
            "Можно хранить реплики в формате JSON. "
            "Например: [{'speaker': 'Anna', 'text': 'Can I have a latte?'}]"
        ),
    )

    characters = models.ManyToManyField(
        StoryCharacter,
        blank=True,
        related_name='scenes',
        verbose_name='Characters',
    )

    media = models.ManyToManyField(
        MediaAsset,
        blank=True,
        related_name='story_scenes',
        verbose_name='Media',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    class Meta:
        ordering = ['episode', 'order', 'title']
        verbose_name = 'Story scene'
        verbose_name_plural = 'Story scenes'

    def __str__(self):
        return f'{self.episode} / Scene {self.order}: {self.title}'


class LessonTemplate(TimeStampedModel):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_templates',
        verbose_name='Topic',
    )

    story_episode = models.ForeignKey(
        StoryEpisode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_templates',
        verbose_name='Story episode',
    )

    title = models.CharField(max_length=255, verbose_name='Title')
    subtitle = models.CharField(max_length=255, blank=True, verbose_name='Subtitle')
    description = models.TextField(blank=True, verbose_name='Description')

    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_templates',
        verbose_name='Level',
    )

    primary_skill = models.CharField(
        max_length=30,
        choices=SKILL_CHOICES,
        default='mixed',
        verbose_name='Primary skill',
    )

    difficulty = models.CharField(
        max_length=30,
        choices=DIFFICULTY_CHOICES,
        default='normal',
        verbose_name='Difficulty',
    )

    objective = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Learning objective',
        help_text='Что пользователь сможет сделать после урока.',
    )

    estimated_minutes = models.PositiveIntegerField(
        default=10,
        verbose_name='Estimated minutes',
    )

    cover_image = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_covers',
        verbose_name='Cover image',
    )

    intro_text = models.TextField(blank=True, verbose_name='Intro text')
    outro_text = models.TextField(blank=True, verbose_name='Outro text')

    personalization_rules = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Personalization rules',
        help_text='Правила, кому и когда лучше показывать этот урок.',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    version = models.PositiveIntegerField(default=1, verbose_name='Version')
    is_premium = models.BooleanField(default=False, verbose_name='Premium only')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    order = models.PositiveIntegerField(default=0, verbose_name='Order')
    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')

    class Meta:
        ordering = ['topic', 'order', 'title']
        verbose_name = 'Lesson template'
        verbose_name_plural = 'Lesson templates'

    def __str__(self):
        return self.title


class LessonBlock(TimeStampedModel):
    lesson_template = models.ForeignKey(
        LessonTemplate,
        on_delete=models.CASCADE,
        related_name='blocks',
        verbose_name='Lesson template',
    )

    story_scene = models.ForeignKey(
        StoryScene,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_blocks',
        verbose_name='Related story scene',
    )

    block_type = models.CharField(
        max_length=40,
        choices=LESSON_BLOCK_TYPE_CHOICES,
        verbose_name='Block type',
    )

    title = models.CharField(max_length=255, blank=True, verbose_name='Title')
    text = models.TextField(blank=True, verbose_name='Text')

    content = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Content JSON',
        help_text='Дополнительные структурированные данные блока.',
    )

    media = models.ManyToManyField(
        MediaAsset,
        blank=True,
        related_name='lesson_blocks',
        verbose_name='Media',
    )

    character = models.ForeignKey(
        StoryCharacter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_blocks',
        verbose_name='Character',
    )

    primary_skill = models.CharField(
        max_length=30,
        choices=SKILL_CHOICES,
        default='mixed',
        verbose_name='Primary skill',
    )

    difficulty = models.CharField(
        max_length=30,
        choices=DIFFICULTY_CHOICES,
        default='normal',
        verbose_name='Difficulty',
    )

    ai_instruction = models.TextField(
        blank=True,
        verbose_name='AI instruction',
        help_text='Если этот блок нужно адаптировать или объяснять через AI.',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    is_optional = models.BooleanField(
        default=False,
        verbose_name='Optional',
        help_text='Можно пропустить при сборке короткого урока.',
    )

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')

    class Meta:
        ordering = ['lesson_template', 'order', 'id']
        verbose_name = 'Lesson block'
        verbose_name_plural = 'Lesson blocks'

    def __str__(self):
        return f'{self.lesson_template} / {self.order}. {self.block_type}'


class ExerciseTemplate(TimeStampedModel):
    lesson_template = models.ForeignKey(
        LessonTemplate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='exercise_templates',
        verbose_name='Lesson template',
    )

    lesson_block = models.ForeignKey(
        LessonBlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercise_templates',
        verbose_name='Lesson block',
    )

    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercise_templates',
        verbose_name='Topic',
    )

    story_episode = models.ForeignKey(
        StoryEpisode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercise_templates',
        verbose_name='Story episode',
    )

    title = models.CharField(max_length=255, blank=True, verbose_name='Title')

    exercise_type = models.CharField(
        max_length=40,
        choices=EXERCISE_TYPE_CHOICES,
        verbose_name='Exercise type',
    )

    prompt = models.TextField(verbose_name='Prompt')
    instruction = models.TextField(blank=True, verbose_name='Instruction')

    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercise_templates',
        verbose_name='Level',
    )

    primary_skill = models.CharField(
        max_length=30,
        choices=SKILL_CHOICES,
        default='mixed',
        verbose_name='Primary skill',
    )

    difficulty = models.CharField(
        max_length=30,
        choices=DIFFICULTY_CHOICES,
        default='normal',
        verbose_name='Difficulty',
    )

    grammar_focus = models.JSONField(default=list, blank=True, verbose_name='Grammar focus')
    vocabulary_focus = models.JSONField(default=list, blank=True, verbose_name='Vocabulary focus')

    media = models.ManyToManyField(
        MediaAsset,
        blank=True,
        related_name='exercise_templates',
        verbose_name='Media',
    )

    correct_answer = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Correct answer',
        help_text=(
            "Для разных типов заданий формат может быть разным. "
            "Например: {'answer': 'drinks'} или {'answers': ['drinks', 'has']}."
        ),
    )

    explanation = models.TextField(
        blank=True,
        verbose_name='Explanation',
        help_text='Объяснение правильного ответа.',
    )

    hints = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Hints',
        help_text='Подсказки, которые можно показывать постепенно.',
    )

    checking_type = models.CharField(
        max_length=30,
        choices=CHECKING_TYPE_CHOICES,
        default='auto_exact',
        verbose_name='Checking type',
    )

    ai_check_prompt = models.TextField(
        blank=True,
        verbose_name='AI check prompt',
        help_text='Инструкция для AI, если задание проверяется AI.',
    )

    points = models.PositiveIntegerField(default=1, verbose_name='Points')
    estimated_seconds = models.PositiveIntegerField(default=60, verbose_name='Estimated seconds')

    order = models.PositiveIntegerField(default=0, verbose_name='Order')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Status',
    )

    version = models.PositiveIntegerField(default=1, verbose_name='Version')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')

    class Meta:
        ordering = ['lesson_template', 'order', 'id']
        verbose_name = 'Exercise template'
        verbose_name_plural = 'Exercise templates'

    def __str__(self):
        if self.title:
            return self.title
        return f'{self.exercise_type}: {self.prompt[:50]}'


class ExerciseOption(TimeStampedModel):
    exercise = models.ForeignKey(
        ExerciseTemplate,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='Exercise',
    )

    text = models.TextField(verbose_name='Option text')

    is_correct = models.BooleanField(default=False, verbose_name='Correct')

    feedback = models.TextField(
        blank=True,
        verbose_name='Feedback',
        help_text='Что показать пользователю, если он выбрал этот вариант.',
    )

    media = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercise_options',
        verbose_name='Media',
    )

    order = models.PositiveIntegerField(default=0, verbose_name='Order')

    class Meta:
        ordering = ['exercise', 'order', 'id']
        verbose_name = 'Exercise option'
        verbose_name_plural = 'Exercise options'

    def __str__(self):
        return f'{self.exercise} / {self.text[:40]}'
