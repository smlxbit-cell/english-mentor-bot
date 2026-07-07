from django.db import migrations, models


def default_target_from_level(apps, schema_editor):
    UserProfile = apps.get_model('users_app', 'UserProfile')
    order = ['a0', 'a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    next_map = {
        'a0': 'A1', 'a1': 'A2', 'a2': 'B1', 'b1': 'B2', 'b2': 'C1', 'c1': 'C2', 'c2': 'C2',
    }
    for profile in UserProfile.objects.exclude(cefr_level='').exclude(cefr_level__isnull=True):
        lv = (profile.cefr_level or '').lower()
        if lv in next_map and not profile.target_cefr_level:
            profile.target_cefr_level = next_map[lv]
            profile.save(update_fields=['target_cefr_level'])


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0012_userprofile_study_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='target_cefr_level',
            field=models.CharField(
                blank=True,
                choices=[
                    ('A1', 'Elementary / A1'),
                    ('A2', 'Pre-Intermediate / A2'),
                    ('B1', 'Intermediate / B1'),
                    ('B2', 'Upper-Intermediate / B2'),
                    ('C1', 'Advanced / C1'),
                    ('C2', 'Proficiency / C2'),
                ],
                help_text='Learner goal CEFR level for the motivation roadmap.',
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='skill_focus',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Skills to emphasise: speaking, listening, reading, writing, grammar, vocabulary.',
            ),
        ),
        migrations.RunPython(default_target_from_level, migrations.RunPython.noop),
    ]
