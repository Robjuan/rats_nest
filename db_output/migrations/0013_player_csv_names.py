# Generated by Django 2.1.3 on 2018-12-24 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0012_auto_20181220_1829'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='csv_names',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]