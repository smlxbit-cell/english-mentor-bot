# Generated manually for UserWordBankStatus

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0002_wordbankentry'),
        ('progress_app', '0002_userrule'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserWordBankStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('known', 'Known'), ('learning', 'Learning'), ('skipped', 'Skipped')],
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bank_entry', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_status',
                    to='learning.wordbankentry',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='word_bank_status',
                    to='users_app.userprofile',
                )),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='userwordbankstatus',
            constraint=models.UniqueConstraint(
                fields=('user', 'bank_entry'),
                name='unique_user_word_bank_status',
            ),
        ),
    ]
