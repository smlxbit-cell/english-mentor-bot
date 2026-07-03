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

    avatar_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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

    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
    )

    title = models.CharField(max_length=150)
    file = models.FileField(upload_to='media_assets/', blank=True, null=True)
    source_url = models.URLField(blank=True)

    license_name = models.CharField(max_length=100, blank=True)
    author = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.media_type}: {self.title}'
