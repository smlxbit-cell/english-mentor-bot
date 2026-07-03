from django.contrib import admin

from .models import Achievement, UserAchievement, UserStats


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'xp_total',
        'level',
        'current_streak',
        'longest_streak',
        'last_study_date',
        'completed_sessions_count',
        'updated_at',
    )
    list_filter = ('level', 'last_study_date', 'updated_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
    )
    readonly_fields = ('updated_at',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'title',
        'xp_reward',
        'is_active',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'title', 'description')
    prepopulated_fields = {'code': ('title',)}


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'achievement',
        'unlocked_at',
    )
    list_filter = ('achievement', 'unlocked_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'achievement__title',
        'achievement__code',
    )
    readonly_fields = ('unlocked_at',)
