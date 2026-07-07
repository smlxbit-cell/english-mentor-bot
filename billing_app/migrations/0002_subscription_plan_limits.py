# Generated manually for tariff plans

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='plan_kind',
            field=models.CharField(
                choices=[('subscription', 'Subscription'), ('voice_addon', 'Voice add-on')],
                default='subscription',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='voice_minutes_monthly',
            field=models.PositiveIntegerField(default=60),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='voice_minutes_in_pack',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='tutor_ai_daily_limit',
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='stt_model',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='sort_order',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='subscriptionplan',
            options={'ordering': ['sort_order', 'price_rub']},
        ),
    ]
