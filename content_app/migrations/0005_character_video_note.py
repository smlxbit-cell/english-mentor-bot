from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_app', '0004_grammarrule'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='speaking_style',
            field=models.CharField(
                blank=True,
                help_text='Short hint for AI dialogue tone, e.g. "simple, warm, short sentences".',
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name='character',
            name='video_note_file_id',
            field=models.CharField(
                blank=True,
                help_text='Telegram file_id for circular video (video note) shown during AI dialogue.',
                max_length=500,
            ),
        ),
        migrations.AlterField(
            model_name='mediaasset',
            name='media_type',
            field=models.CharField(
                choices=[
                    ('image', 'Image'),
                    ('audio', 'Audio'),
                    ('video', 'Video'),
                    ('video_note', 'Video note (circle)'),
                    ('gif', 'GIF / animation'),
                ],
                max_length=20,
            ),
        ),
    ]
