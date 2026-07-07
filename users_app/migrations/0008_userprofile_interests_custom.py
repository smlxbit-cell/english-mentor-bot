from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0007_userprofile_learning_goal_custom'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='interests_custom',
            field=models.CharField(
                blank=True,
                help_text='Comma-separated custom interests typed by the learner.',
                max_length=500,
            ),
        ),
    ]
