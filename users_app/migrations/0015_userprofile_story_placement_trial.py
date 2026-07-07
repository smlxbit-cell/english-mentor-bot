from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0014_userprofile_speaking_anxiety'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='story_placement_applied',
            field=models.BooleanField(
                default=False,
                help_text='Serial episodes below level were auto-skipped.',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='trial_started_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the 2-day full app trial began.',
                null=True,
            ),
        ),
    ]
