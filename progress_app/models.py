from django.db import models


class UserWordProgress(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        LEARNING = 'learning', 'Learning'
        KNOWN = 'known', 'Known'
        MASTERED = 'mastered', 'Mastered'

    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='word_progress',
    )

    word = models.ForeignKey(
        'learning.Word',
        on_delete=models.CASCADE,
        related_name='user_progress',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)

    strength = models.FloatField(default=0.0)

    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    next_review_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_review_at', '-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'word'],
                name='unique_user_word_progress',
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.word}'


class SkillProgress(models.Model):
    class Skill(models.TextChoices):
        VOCABULARY = 'vocabulary', 'Vocabulary'
        LISTENING = 'listening', 'Listening'
        SPEAKING = 'speaking', 'Speaking'
        GRAMMAR = 'grammar', 'Grammar'
        READING = 'reading', 'Reading'
        WRITING = 'writing', 'Writing'
        PRONUNCIATION = 'pronunciation', 'Pronunciation'

    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='skill_progress',
    )

    skill = models.CharField(
        max_length=30,
        choices=Skill.choices,
    )

    score = models.FloatField(default=0.0)

    attempts_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    wrong_count = models.PositiveIntegerField(default=0)

    last_practiced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['user', 'skill']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'skill'],
                name='unique_user_skill_progress',
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.skill}: {self.score}'


class ErrorLog(models.Model):
    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='error_logs',
    )

    answer = models.ForeignKey(
        'study_app.UserAnswer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs',
    )

    skill = models.CharField(max_length=30, blank=True)
    error_type = models.CharField(max_length=100, blank=True)

    original_text = models.TextField(blank=True)
    corrected_text = models.TextField(blank=True)
    explanation = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.error_type}'
