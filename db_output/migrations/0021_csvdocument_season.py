# Generated by Django 2.1.3 on 2019-01-25 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0020_auto_20190123_0404'),
    ]

    operations = [
        migrations.AddField(
            model_name='csvdocument',
            name='season',
            field=models.IntegerField(default=2018),
            preserve_default=False,
        ),
    ]