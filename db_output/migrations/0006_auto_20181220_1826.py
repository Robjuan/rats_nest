# Generated by Django 2.1.3 on 2018-12-20 18:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0005_players_nickname'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Players',
            new_name='Player',
        ),
    ]
