from django.db import migrations, models


def migrate_legacy_schedule(apps, schema_editor):
    UserProfile = apps.get_model('users_app', 'UserProfile')
    for profile in UserProfile.objects.all():
        updates = {}
        if profile.daily_minutes <= 10:
            updates['daily_minutes'] = 20
        if profile.onboarding_status == 'completed':
            updates['study_schedule_set'] = True
        if updates:
            UserProfile.objects.filter(pk=profile.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0011_userprofile_tutor_usage'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='rest_weekday',
            field=models.PositiveSmallIntegerField(
                default=6,
                help_text='Weekday for light rest (0=Mon … 6=Sun). Default Sunday.',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='study_days_per_week',
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text='Target training days per week (3–7).',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='study_schedule_set',
            field=models.BooleanField(
                default=False,
                help_text='User chose daily minutes and weekly schedule in onboarding.',
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='daily_minutes',
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text='Daily training budget: 20, 30, or 60 minutes.',
            ),
        ),
        migrations.RunPython(migrate_legacy_schedule, migrations.RunPython.noop),
    ]
