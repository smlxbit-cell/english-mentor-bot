from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_app', '0006_charactermedia'),
    ]

    operations = [
        migrations.AddField(
            model_name='charactermedia',
            name='source_path',
            field=models.CharField(
                blank=True,
                help_text='Relative path under media/spirit/ for re-sync',
                max_length=255,
            ),
        ),
    ]
