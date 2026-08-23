from django.contrib import admin

from .models import Word, WordBankEntry


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


@admin.register(WordBankEntry)
class WordBankEntryAdmin(admin.ModelAdmin):
    list_display = (
        'english',
        'translation',
        'cefr_level',
        'part_of_speech',
        'is_active',
    )
    list_filter = (
        'cefr_level',
        'is_active',
        'part_of_speech',
    )
    search_fields = (
        'english',
        'translation',
        'slug',
    )
    ordering = (
        'cefr_level',
        'english',
    )
