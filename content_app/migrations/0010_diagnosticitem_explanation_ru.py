from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_app', '0009_charactermedia_video_note_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosticitem',
            name='explanation_ru',
            field=models.TextField(
                blank=True,
                help_text='Short tip shown when the learner answers wrong.',
            ),
        ),
    ]
