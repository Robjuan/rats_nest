# Generated by Django 2.1.3 on 2018-12-20 18:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0010_auto_20181220_1828'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Possessions',
            new_name='Possession',
        ),
    ]