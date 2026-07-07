from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0008_userprofile_interests_custom'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='profession_custom',
            field=models.CharField(
                blank=True,
                help_text='Free-text sphere when profession is «other».',
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='profession',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ecommerce', 'Онлайн-магазины'),
                    ('it', 'IT / разработка'),
                    ('hospitality', 'Отели / туризм'),
                    ('food', 'Кафе / рестораны'),
                    ('education', 'Образование'),
                    ('medicine', 'Медицина'),
                    ('finance', 'Финансы'),
                    ('marketing', 'Маркетинг'),
                    ('psychology', 'Психология'),
                    ('design', 'Дизайн'),
                    ('law', 'Юриспруденция'),
                    ('logistics', 'Логистика'),
                    ('student', 'Пока только учусь'),
                    ('other', '✍️ Написать свою сферу'),
                ],
                help_text='Professional sphere used to bias personalized content.',
                max_length=30,
            ),
        ),
    ]
