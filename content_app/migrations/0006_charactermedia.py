from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content_app', '0005_character_video_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='CharacterMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField(help_text='e.g. greeting, joy, scene_cafe', max_length=60)),
                ('kind', models.CharField(
                    choices=[
                        ('animation', 'GIF / short MP4'),
                        ('image', 'Photo'),
                        ('video_note', 'Circle video'),
                    ],
                    default='animation',
                    max_length=20,
                )),
                ('title', models.CharField(blank=True, max_length=150)),
                ('telegram_file_id', models.CharField(blank=True, max_length=500)),
                ('file', models.FileField(blank=True, null=True, upload_to='character_media/')),
                ('character', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='media_clips',
                    to='content_app.character',
                )),
            ],
            options={
                'ordering': ['character', 'key'],
                'unique_together': {('character', 'key')},
            },
        ),
    ]
