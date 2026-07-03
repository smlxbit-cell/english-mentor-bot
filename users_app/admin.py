from django.contrib import admin

from .models import Interest, UserInterest, UserProfile


class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 1


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
        'daily_minutes',
        'onboarding_status',
        'is_active',
        'created_at',
    )
    list_filter = (
        'cefr_level',
        'learning_goal',
        'onboarding_status',
        'is_active',
        'created_at',
    )
    search_fields = (
        'telegram_id',
        'telegram_username',
        'first_name',
        'last_name',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [UserInterestInline]


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'interest', 'weight', 'created_at')
    list_filter = ('interest', 'created_at')
    search_fields = (
        'user__telegram_username',
        'user__first_name',
        'interest__name',
    )
