# Generated by Django 2.1.3 on 2019-04-12 15:34

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0032_auto_20190409_0127'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='team',
            managers=[
                ('with_games', django.db.models.manager.Manager()),
            ],
        ),
    ]
