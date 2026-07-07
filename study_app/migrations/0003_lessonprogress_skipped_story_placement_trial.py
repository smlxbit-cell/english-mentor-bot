# Generated migration for story placement + skipped lessons

from django.db import migrations, models


def backfill_placement_for_high_levels(apps, schema_editor):
    UserProfile = apps.get_model('users_app', 'UserProfile')
    Lesson = apps.get_model('content_app', 'Lesson')
    LessonProgress = apps.get_model('study_app', 'LessonProgress')

    target_titles = {
        'B1': 'Hotel Check-in',
        'B2': 'First Day at Work',
        'C1': 'First Day at Work',
        'C2': 'First Day at Work',
    }
    for profile in UserProfile.objects.filter(cefr_level__in=target_titles):
        title = target_titles.get(profile.cefr_level)
        if not title:
            continue
        target = Lesson.objects.filter(title=title, is_published=True).first()
        if not target:
            continue
        completed = LessonProgress.objects.filter(
            user_id=profile.id,
            status='completed',
        ).exists()
        if completed:
            profile.story_placement_applied = True
            profile.save(update_fields=['story_placement_applied'])
            continue
        for lesson in Lesson.objects.filter(is_published=True).order_by('id'):
            if lesson.id == target.id:
                break
            LessonProgress.objects.get_or_create(
                user_id=profile.id,
                lesson_id=lesson.id,
                defaults={'status': 'skipped'},
            )
        profile.story_placement_applied = True
        profile.save(update_fields=['story_placement_applied'])


class Migration(migrations.Migration):

    dependencies = [
        ('study_app', '0002_stepattempt_lessonprogress'),
        ('users_app', '0015_userprofile_story_placement_trial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lessonprogress',
            name='status',
            field=models.CharField(
                choices=[
                    ('in_progress', 'In progress'),
                    ('completed', 'Completed'),
                    ('skipped', 'Skipped (placement)'),
                ],
                default='in_progress',
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_placement_for_high_levels, migrations.RunPython.noop),
    ]
