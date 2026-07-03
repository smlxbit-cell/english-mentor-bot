from django.contrib import admin

from .models import DailySession, DailySessionBlock, UserAnswer


class DailySessionBlockInline(admin.TabularInline):
    model = DailySessionBlock
    extra = 0
    fields = (
        'order',
        'block_type',
        'skill',
        'title',
        'xp_reward',
        'is_completed',
    )
    show_change_link = True


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    fields = (
        'block',
        'answer_text',
        'is_correct',
        'score',
        'answered_at',
    )
    readonly_fields = ('answered_at',)
    show_change_link = True


@admin.register(DailySession)
class DailySessionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'date',
        'title',
        'theme',
        'story_episode',
        'status',
        'xp_earned',
        'created_at',
    )
    list_filter = ('status', 'date', 'theme', 'created_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'title',
        'intro_text',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DailySessionBlockInline, UserAnswerInline]


@admin.register(DailySessionBlock)
class DailySessionBlockAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'session',
        'order',
        'block_type',
        'skill',
        'title',
        'xp_reward',
        'is_completed',
        'created_at',
    )
    list_filter = ('block_type', 'skill', 'is_completed', 'created_at')
    search_fields = (
        'session__user__telegram_username',
        'session__user__first_name',
        'title',
        'correct_answer',
        'explanation',
    )


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'session',
        'block',
        'is_correct',
        'score',
        'answered_at',
    )
    list_filter = ('is_correct', 'answered_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'answer_text',
        'feedback',
        'corrected_text',
    )
    readonly_fields = ('answered_at',)
