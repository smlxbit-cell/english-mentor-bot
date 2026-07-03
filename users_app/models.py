from django.db import models


class Interest(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class CefrLevel(models.TextChoices):
        A0 = 'A0', 'Beginner / A0'
        A1 = 'A1', 'Elementary / A1'
        A2 = 'A2', 'Pre-Intermediate / A2'
        B1 = 'B1', 'Intermediate / B1'
        B2 = 'B2', 'Upper-Intermediate / B2'
        C1 = 'C1', 'Advanced / C1'
        C2 = 'C2', 'Proficiency / C2'

    class LearningGoal(models.TextChoices):
        TRAVEL = 'travel', 'Travel'
        WORK = 'work', 'Work'
        STUDY = 'study', 'Study'
        MOVIES = 'movies', 'Movies and series'
        RELOCATION = 'relocation', 'Relocation'
        COMMUNICATION = 'communication', 'Communication'
        EXAMS = 'exams', 'Exams'
        OTHER = 'other', 'Other'

    class OnboardingStatus(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    cefr_level = models.CharField(
        max_length=2,
        choices=CefrLevel.choices,
        blank=True,
    )

    learning_goal = models.CharField(
        max_length=30,
        choices=LearningGoal.choices,
        blank=True,
    )

    daily_minutes = models.PositiveSmallIntegerField(default=10)

    onboarding_status = models.CharField(
        max_length=30,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.NOT_STARTED,
    )

    interests = models.ManyToManyField(
        Interest,
        through='UserInterest',
        blank=True,
        related_name='users',
    )

    preferred_formats = models.JSONField(default=list, blank=True)

    current_story_day = models.PositiveIntegerField(default=1)
    timezone = models.CharField(max_length=50, default='UTC')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.telegram_username:
            return f'@{self.telegram_username}'
        if self.first_name:
            return self.first_name
        return f'User {self.id}'


class UserInterest(models.Model):
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='user_interests',
    )
    interest = models.ForeignKey(
        Interest,
        on_delete=models.CASCADE,
        related_name='user_interests',
    )

    weight = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'interest'],
                name='unique_user_interest',
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.interest}'
