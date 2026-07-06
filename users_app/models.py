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

    class Sphere(models.TextChoices):
        ECOMMERCE = 'ecommerce', 'E-commerce'
        IT = 'it', 'IT / разработка'
        HOSPITALITY = 'hospitality', 'Отели / туризм'
        FOOD = 'food', 'Кафе / рестораны'
        EDUCATION = 'education', 'Образование'
        PSYCHOLOGY = 'psychology', 'Психология'
        MEDICINE = 'medicine', 'Медицина'
        FINANCE = 'finance', 'Финансы'
        MARKETING = 'marketing', 'Маркетинг'
        OTHER = 'other', 'Другое'

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

    profession = models.CharField(
        max_length=30,
        choices=Sphere.choices,
        blank=True,
        help_text='Professional sphere used to bias personalized content.',
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
    timezone = models.CharField(max_length=50, default='Europe/Moscow')

    notifications_enabled = models.BooleanField(
        default=False,
        help_text='Send daily training reminders via Telegram.',
    )
    reminder_time = models.TimeField(
        null=True, blank=True,
        help_text='Local reminder time (uses timezone field).',
    )
    reminder_setup_done = models.BooleanField(
        default=False,
        help_text='User was asked about notifications (do not re-prompt).',
    )

    # Diagnostic + trial state (free funnel before subscription).
    diagnostic_completed = models.BooleanField(default=False)
    trial_lessons_used = models.PositiveIntegerField(default=0)
    weak_skills = models.JSONField(
        default=list, blank=True,
        help_text="Skills to focus on, e.g. ['listening', 'grammar'].",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(
        null=True, blank=True,
        help_text='Updated on every bot interaction (not just /start).',
    )
    last_inactive_nudge_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Last “we miss you” message sent after 7+ days away.',
    )

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
