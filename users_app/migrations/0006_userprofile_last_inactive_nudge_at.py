from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0005_userprofile_notifications_enabled_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_inactive_nudge_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Last “we miss you” message sent after 7+ days away.',
                null=True,
            ),
        ),
    ]
