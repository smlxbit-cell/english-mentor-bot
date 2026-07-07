# Generated manually for voice usage tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0009_userprofile_profession_custom'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='voice_bonus_seconds',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='voice_seconds_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='voice_usage_period',
            field=models.CharField(blank=True, max_length=7),
        ),
    ]
