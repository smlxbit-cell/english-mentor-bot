from django.contrib import admin

from .models import Payment, Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'price_rub', 'duration_days', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    prepopulated_fields = {'code': ('name',)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'status', 'started_at', 'expires_at')
    list_filter = ('status', 'plan', 'expires_at')
    search_fields = ('user__telegram_username', 'user__first_name')
    readonly_fields = ('created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'plan', 'provider', 'status', 'amount_rub', 'created_at',
    )
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('user__telegram_username', 'user__first_name', 'payload')
    readonly_fields = ('created_at',)
