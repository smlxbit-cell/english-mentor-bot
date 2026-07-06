from django.contrib import admin

from billing_app.models import Subscription
from gamification_app.models import UserAchievement, UserStats
from study_app.models import LessonProgress, StepAttempt

from .models import Interest, UserInterest, UserProfile


class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 1


class UserStatsInline(admin.StackedInline):
    model = UserStats
    can_delete = False
    extra = 0
    readonly_fields = (
        'xp_total', 'level', 'current_streak', 'longest_streak',
        'last_study_date', 'completed_sessions_count', 'updated_at',
    )


class LessonProgressInline(admin.TabularInline):
    model = LessonProgress
    extra = 0
    can_delete = False
    fields = ('lesson', 'status', 'current_step_index', 'correct_count',
              'total_answered', 'xp_earned', 'started_at', 'completed_at')
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class StepAttemptInline(admin.TabularInline):
    model = StepAttempt
    extra = 0
    can_delete = False
    fields = ('lesson', 'step', 'is_correct', 'score', 'used_ai', 'method',
              'answer_text', 'created_at')
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 0
    can_delete = False
    fields = ('achievement', 'unlocked_at')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    can_delete = False
    fields = ('plan', 'status', 'started_at', 'expires_at')
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'telegram_id',
        'telegram_username',
        'first_name',
        'cefr_level',
        'learning_goal',
        'profession',
        'onboarding_status',
        'diagnostic_completed',
        'trial_lessons_used',
        'is_active',
        'last_seen',
        'created_at',
    )
    list_filter = (
        'cefr_level',
        'learning_goal',
        'profession',
        'onboarding_status',
        'diagnostic_completed',
        'is_active',
        'created_at',
    )
    search_fields = (
        'telegram_id',
        'telegram_username',
        'first_name',
        'last_name',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'last_seen')
    inlines = [
        UserInterestInline,
        UserStatsInline,
        SubscriptionInline,
        LessonProgressInline,
        StepAttemptInline,
        UserAchievementInline,
    ]


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'interest', 'weight', 'created_at')
    list_filter = ('interest', 'created_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'interest__name',
    )
