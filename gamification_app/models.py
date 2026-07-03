from django.db import models


class UserStats(models.Model):
    user = models.OneToOneField(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='stats',
    )

    xp_total = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)

    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)

    last_study_date = models.DateField(null=True, blank=True)

    completed_sessions_count = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user} — XP: {self.xp_total}'


class Achievement(models.Model):
    code = models.SlugField(max_length=100, unique=True)

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    icon = models.CharField(max_length=20, blank=True)

    xp_reward = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    user = models.ForeignKey(
        'users_app.UserProfile',
        on_delete=models.CASCADE,
        related_name='achievements',
    )

    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements',
    )

    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-unlocked_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'achievement'],
                name='unique_user_achievement',
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.achievement}'
