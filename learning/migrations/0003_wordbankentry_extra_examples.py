from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0002_wordbankentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='wordbankentry',
            name='extra_examples',
            field=models.JSONField(blank=True, default=list, verbose_name='Доп. примеры'),
        ),
    ]
