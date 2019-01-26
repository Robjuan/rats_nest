# Generated by Django 2.1.3 on 2019-01-26 22:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0022_auto_20190125_2148'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='player',
            options={'ordering': ('proper_name',)},
        ),
        migrations.AddField(
            model_name='game',
            name='verified',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='player',
            name='numbers',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]