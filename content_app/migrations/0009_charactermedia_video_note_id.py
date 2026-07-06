from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_app', '0008_alter_charactermedia_source_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='charactermedia',
            name='note_source_path',
            field=models.CharField(
                blank=True,
                help_text='Square clip under media/spirit/notes/ for video note.',
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name='charactermedia',
            name='telegram_video_note_id',
            field=models.CharField(
                blank=True,
                help_text='Circular video note file_id (compact, for welcome / menus).',
                max_length=500,
            ),
        ),
    ]
