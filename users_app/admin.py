from django.contrib import admin
from django.utils import timezone

from billing_app.models import Payment, Subscription
from billing_app.trial_access import access_tier_label
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


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    fields = ('plan', 'amount_rub', 'provider', 'status', 'created_at')
    readonly_fields = fields
    show_change_link = True

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


def billing_tier(profile: UserProfile) -> str:
    from billing_app.trial_access import access_tier_label

    return access_tier_label(profile)


def active_sub_until(profile: UserProfile) -> str:
    sub = Subscription.objects.filter(
        user_id=profile.id,
        status=Subscription.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    ).order_by('-expires_at').first()
    if not sub:
        return '—'
    return f'{sub.plan.code} → {sub.expires_at:%d.%m.%Y}'


billing_tier.short_description = 'Тариф'
active_sub_until.short_description = 'Подписка до'


class BillingTierFilter(admin.SimpleListFilter):
    title = 'тариф доступа'
    parameter_name = 'billing_tier'

    def lookups(self, request, model_admin):
        return (
            ('free', 'Free'),
            ('trial', 'Пробный'),
            ('paid', 'Платный'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        matched = [p.pk for p in queryset if access_tier_label(p) == value]
        return queryset.filter(pk__in=matched)


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
        billing_tier,
        active_sub_until,
        'trial_lessons_used',
        'is_active',
        'last_seen',
        'created_at',
    )
    list_filter = (
        BillingTierFilter,
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
        PaymentInline,
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
