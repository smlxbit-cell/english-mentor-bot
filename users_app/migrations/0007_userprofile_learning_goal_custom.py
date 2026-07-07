from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0006_userprofile_last_inactive_nudge_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='learning_goal_custom',
            field=models.CharField(
                blank=True,
                help_text='Free-text goal when learning_goal is «other».',
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='learning_goal',
            field=models.CharField(
                blank=True,
                choices=[
                    ('travel', 'Путешествия'),
                    ('work', 'Работа'),
                    ('study', 'Учёба'),
                    ('movies', 'Фильмы и сериалы'),
                    ('relocation', 'Переезд'),
                    ('communication', 'Общение'),
                    ('exams', 'Экзамены'),
                    ('personal', 'Для себя'),
                    ('other', 'Своё'),
                ],
                max_length=30,
            ),
        ),
    ]
