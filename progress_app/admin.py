from django.contrib import admin

from .models import ErrorLog, SkillProgress, UserWordProgress


@admin.register(UserWordProgress)
class UserWordProgressAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'word',
        'status',
        'correct_count',
        'wrong_count',
        'strength',
        'last_reviewed_at',
        'next_review_at',
    )
    list_filter = ('status', 'last_reviewed_at', 'next_review_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'word__english',
        'word__translation',
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SkillProgress)
class SkillProgressAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'skill',
        'score',
        'attempts_count',
        'correct_count',
        'wrong_count',
        'last_practiced_at',
    )
    list_filter = ('skill', 'last_practiced_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'skill',
    )


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'skill',
        'error_type',
        'created_at',
    )
    list_filter = ('skill', 'error_type', 'created_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'original_text',
        'corrected_text',
        'explanation',
    )
