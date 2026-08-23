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


class WordBankEntry(models.Model):
    """Справочный банк слов A1–C1 (кorpus). Пользователь добавляет отсюда в свой словарь."""

    class CEFRLevel(models.TextChoices):
        A1 = 'a1', 'A1'
        A2 = 'a2', 'A2'
        B1 = 'b1', 'B1'
        B2 = 'b2', 'B2'
        C1 = 'c1', 'C1'

    slug = models.SlugField(max_length=140, unique=True, verbose_name='Ключ')
    english = models.CharField(max_length=120, db_index=True, verbose_name='English')
    translation = models.CharField(max_length=200, verbose_name='Перевод')
    example = models.TextField(blank=True, verbose_name='Пример (EN)')
    example_ru = models.TextField(blank=True, verbose_name='Пример (RU)')
    cefr_level = models.CharField(
        max_length=2,
        choices=CEFRLevel.choices,
        db_index=True,
        verbose_name='Уровень CEFR',
    )
    part_of_speech = models.CharField(max_length=30, blank=True, verbose_name='Часть речи')
    topics = models.JSONField(default=list, blank=True, verbose_name='Темы')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cefr_level', 'english']
        verbose_name = 'Слово банка'
        verbose_name_plural = 'Банк слов'
        indexes = [
            models.Index(fields=['cefr_level', 'english']),
        ]

    def __str__(self):
        return f'{self.english} ({self.cefr_level.upper()}) — {self.translation}'
