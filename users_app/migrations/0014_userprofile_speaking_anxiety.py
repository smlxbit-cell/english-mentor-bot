from django.db import migrations, models


def backfill_skill_focus_confirmed(apps, schema_editor):
    UserProfile = apps.get_model('users_app', 'UserProfile')
    UserProfile.objects.filter(study_schedule_set=True).update(skill_focus_confirmed=True)


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0013_userprofile_target_cefr_skill_focus'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='speaking_anxiety',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Not asked'),
                    ('high', 'High — afraid to speak'),
                    ('mild', 'Mild — some nervousness'),
                    ('none', 'None'),
                ],
                default='',
                help_text='Self-reported speaking barrier after diagnostic.',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='skill_focus_confirmed',
            field=models.BooleanField(
                default=False,
                help_text='User confirmed skill focus step in onboarding.',
            ),
        ),
        migrations.RunPython(backfill_skill_focus_confirmed, migrations.RunPython.noop),
    ]
