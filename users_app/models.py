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
        TRAVEL = 'travel', 'Путешествия'
        WORK = 'work', 'Работа'
        STUDY = 'study', 'Учёба'
        MOVIES = 'movies', 'Фильмы и сериалы'
        RELOCATION = 'relocation', 'Переезд'
        COMMUNICATION = 'communication', 'Общение'
        EXAMS = 'exams', 'Экзамены'
        PERSONAL = 'personal', 'Для себя'
        OTHER = 'other', '✍️ Написать свою цель'

    class OnboardingStatus(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not started'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    class Sphere(models.TextChoices):
        ECOMMERCE = 'ecommerce', 'Онлайн-магазины'
        IT = 'it', 'IT / разработка'
        HOSPITALITY = 'hospitality', 'Отели / туризм'
        FOOD = 'food', 'Кафе / рестораны'
        EDUCATION = 'education', 'Образование'
        MEDICINE = 'medicine', 'Медицина'
        FINANCE = 'finance', 'Финансы'
        MARKETING = 'marketing', 'Маркетинг'
        PSYCHOLOGY = 'psychology', 'Психология'
        DESIGN = 'design', 'Дизайн'
        LAW = 'law', 'Юриспруденция'
        LOGISTICS = 'logistics', 'Логистика'
        STUDENT = 'student', 'Пока только учусь'
        OTHER = 'other', '✍️ Написать свою сферу'

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    cefr_level = models.CharField(
        max_length=2,
        choices=CefrLevel.choices,
        blank=True,
    )

    target_cefr_level = models.CharField(
        max_length=2,
        choices=[
            ('A1', 'A1'),
            ('A2', 'A2'),
            ('B1', 'B1'),
            ('B2', 'B2'),
            ('C1', 'C1'),
            ('C2', 'C2'),
        ],
        blank=True,
        help_text='Goal CEFR level for the motivation roadmap.',
    )

    skill_focus = models.JSONField(
        default=list,
        blank=True,
        help_text='Skills to emphasise: speaking, listening, reading, writing, grammar, vocabulary.',
    )

    class SpeakingAnxiety(models.TextChoices):
        HIGH = 'high', 'High — afraid to speak'
        MILD = 'mild', 'Mild — some nervousness'
        NONE = 'none', 'None'

    speaking_anxiety = models.CharField(
        max_length=10,
        choices=SpeakingAnxiety.choices,
        blank=True,
        default='',
        help_text='Self-reported speaking barrier after diagnostic.',
    )

    skill_focus_confirmed = models.BooleanField(
        default=False,
        help_text='User confirmed skill focus step in onboarding.',
    )

    story_placement_applied = models.BooleanField(
        default=False,
        help_text='Serial episodes below level were auto-skipped.',
    )

    trial_started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the 2-day full app trial began.',
    )

    learning_goal = models.CharField(
        max_length=30,
        choices=LearningGoal.choices,
        blank=True,
    )

    learning_goal_custom = models.CharField(
        max_length=200,
        blank=True,
        help_text='Free-text goal when learning_goal is «other».',
    )

    profession = models.CharField(
        max_length=30,
        choices=Sphere.choices,
        blank=True,
        help_text='Professional sphere used to bias personalized content.',
    )

    profession_custom = models.CharField(
        max_length=200,
        blank=True,
        help_text='Free-text sphere when profession is «other».',
    )

    daily_minutes = models.PositiveSmallIntegerField(
        default=20,
        help_text='Daily training budget: 20, 30, or 60 minutes.',
    )

    study_days_per_week = models.PositiveSmallIntegerField(
        default=5,
        help_text='Target training days per week (3–7).',
    )

    rest_weekday = models.PositiveSmallIntegerField(
        default=6,
        help_text='Weekday for light rest (0=Mon … 6=Sun). Default Sunday.',
    )

    study_schedule_set = models.BooleanField(
        default=False,
        help_text='User chose daily minutes and weekly schedule in onboarding.',
    )

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

    interests_custom = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated custom interests typed by the learner.',
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

    voice_seconds_used = models.PositiveIntegerField(
        default=0,
        help_text='Voice seconds consumed in the current voice_usage_period.',
    )
    voice_bonus_seconds = models.PositiveIntegerField(
        default=0,
        help_text='Extra voice seconds from purchased add-on packs.',
    )
    voice_usage_period = models.CharField(
        max_length=7,
        blank=True,
        help_text='YYYY-MM for monthly voice quota reset.',
    )

    tutor_messages_used = models.PositiveIntegerField(
        default=0,
        help_text='Tutor text replies used in tutor_usage_period.',
    )
    tutor_usage_period = models.CharField(
        max_length=7,
        blank=True,
        help_text='YYYY-MM for monthly tutor message quota reset.',
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
