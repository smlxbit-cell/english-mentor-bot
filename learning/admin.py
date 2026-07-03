from django.contrib import admin

from .models import Word


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = (
        'english',
        'translation',
        'difficulty',
        'created_at',
    )

    list_filter = (
        'difficulty',
        'created_at',
    )

    search_fields = (
        'english',
        'translation',
    )

    ordering = (
        'english',
    )
