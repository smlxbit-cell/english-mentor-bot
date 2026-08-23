# Generated manually for WordBankEntry

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordBankEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=140, unique=True, verbose_name='Ключ')),
                ('english', models.CharField(db_index=True, max_length=120, verbose_name='English')),
                ('translation', models.CharField(max_length=200, verbose_name='Перевод')),
                ('example', models.TextField(blank=True, verbose_name='Пример (EN)')),
                ('example_ru', models.TextField(blank=True, verbose_name='Пример (RU)')),
                ('cefr_level', models.CharField(
                    choices=[('a1', 'A1'), ('a2', 'A2'), ('b1', 'B1'), ('b2', 'B2'), ('c1', 'C1')],
                    db_index=True,
                    max_length=2,
                    verbose_name='Уровень CEFR',
                )),
                ('part_of_speech', models.CharField(blank=True, max_length=30, verbose_name='Часть речи')),
                ('topics', models.JSONField(blank=True, default=list, verbose_name='Темы')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Слово банка',
                'verbose_name_plural': 'Банк слов',
                'ordering': ['cefr_level', 'english'],
            },
        ),
        migrations.AddIndex(
            model_name='wordbankentry',
            index=models.Index(fields=['cefr_level', 'english'], name='learning_wo_cefr_le_6a8f2d_idx'),
        ),
    ]
