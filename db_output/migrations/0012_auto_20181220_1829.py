# Generated by Django 2.1.3 on 2018-12-20 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0011_auto_20181220_1828'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PossessionEvents',
            new_name='Event',
        ),
    ]
