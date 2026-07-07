# Generated manually for monthly tutor message tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0010_userprofile_voice_usage'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='tutor_messages_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='tutor_usage_period',
            field=models.CharField(blank=True, max_length=7),
        ),
    ]
