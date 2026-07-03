from django.db import models


class Word(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Легкое'
        MEDIUM = 'medium', 'Среднее'
        HARD = 'hard', 'Сложное'

    english = models.CharField(
        max_length=100,
        verbose_name='Слово на английском',
    )

    translation = models.CharField(
        max_length=100,
        verbose_name='Перевод',
    )

    example = models.TextField(
        blank=True,
        verbose_name='Пример использования',
    )

    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
        verbose_name='Сложность',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    class Meta:
        ordering = ['english']
        verbose_name = 'Слово'
        verbose_name_plural = 'Слова'

    def __str__(self):
        return f'{self.english} — {self.translation}'
