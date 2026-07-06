from django.db import models


class DailySession(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        SKIPPED = 'skipped', 'Skipped'

    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='daily_sessions',
    )

    date = models.DateField()

    theme = models.ForeignKey(
        'content_app.ContentTheme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_sessions',
    )

    story_episode = models.ForeignKey(
        'content_app.StoryEpisode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_sessions',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    title = models.CharField(max_length=150, blank=True)
    intro_text = models.TextField(blank=True)

    xp_earned = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'date'],
                name='unique_daily_session_per_user_date',
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.date}'


class DailySessionBlock(models.Model):
    class BlockType(models.TextChoices):
        STORY = 'story', 'Story'
        VOCABULARY = 'vocabulary', 'Vocabulary'
        QUIZ = 'quiz', 'Quiz'
        LISTENING = 'listening', 'Listening'
        SPEAKING = 'speaking', 'Speaking'
        PHOTO = 'photo', 'Photo'
        DIALOGUE = 'dialogue', 'Dialogue'
        SHADOWING = 'shadowing', 'Shadowing'
        GRAMMAR = 'grammar', 'Grammar'
        REFLECTION = 'reflection', 'Reflection'

    class Skill(models.TextChoices):
        VOCABULARY = 'vocabulary', 'Vocabulary'
        LISTENING = 'listening', 'Listening'
        SPEAKING = 'speaking', 'Speaking'
        GRAMMAR = 'grammar', 'Grammar'
        READING = 'reading', 'Reading'
        WRITING = 'writing', 'Writing'
        PRONUNCIATION = 'pronunciation', 'Pronunciation'

    session = models.ForeignKey(
        DailySession,
        on_delete=models.CASCADE,
        related_name='blocks',
    )

    order = models.PositiveSmallIntegerField()

    block_type = models.CharField(
        max_length=30,
        choices=BlockType.choices,
    )

    skill = models.CharField(
        max_length=30,
        choices=Skill.choices,
        blank=True,
    )

    title = models.CharField(max_length=150, blank=True)

    content = models.JSONField(default=dict, blank=True)

    correct_answer = models.TextField(blank=True)
    explanation = models.TextField(blank=True)

    xp_reward = models.PositiveIntegerField(default=10)

    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'order'],
                name='unique_block_order_in_session',
            )
        ]

    def __str__(self):
        return f'{self.session} — {self.order}. {self.block_type}'


class UserAnswer(models.Model):
    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='answers',
    )

    session = models.ForeignKey(
        DailySession,
        on_delete=models.CASCADE,
        related_name='answers',
    )

    block = models.ForeignKey(
        DailySessionBlock,
        on_delete=models.CASCADE,
        related_name='answers',
    )

    answer_text = models.TextField(blank=True)
    answer_payload = models.JSONField(default=dict, blank=True)

    is_correct = models.BooleanField(null=True, blank=True)

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    feedback = models.TextField(blank=True)
    corrected_text = models.TextField(blank=True)
    detected_errors = models.JSONField(default=list, blank=True)

    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-answered_at']

    def __str__(self):
        return f'{self.user} — {self.block}'


class LessonProgress(models.Model):
    """Per-user progress through a content_app.Lesson."""

    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='lesson_progress',
    )
    lesson = models.ForeignKey(
        'content_app.Lesson',
        on_delete=models.CASCADE,
        related_name='user_progress',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    current_step_index = models.PositiveIntegerField(default=0)

    correct_count = models.PositiveIntegerField(default=0)
    total_answered = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'lesson'],
                name='unique_user_lesson_progress',
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.lesson} ({self.status})'


class StepAttempt(models.Model):
    """A learner's answer to one interactive LessonStep (for analytics/feedback)."""

    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='step_attempts',
    )
    lesson = models.ForeignKey(
        'content_app.Lesson',
        on_delete=models.CASCADE,
        related_name='step_attempts',
    )
    step = models.ForeignKey(
        'content_app.LessonStep',
        on_delete=models.CASCADE,
        related_name='attempts',
    )

    answer_text = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    used_ai = models.BooleanField(default=False)
    method = models.CharField(max_length=30, blank=True)
    feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — step {self.step_id}'
