# Generated manually for monthly tutor message limits

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing_app', '0002_subscription_plan_limits'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='tutor_ai_monthly_limit',
            field=models.PositiveIntegerField(default=500),
        ),
        migrations.AlterField(
            model_name='subscriptionplan',
            name='tutor_ai_daily_limit',
            field=models.PositiveIntegerField(
                default=80,
                help_text='Soft anti-spam cap per calendar day (not the main tutor budget).',
            ),
        ),
    ]
