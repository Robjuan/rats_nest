# Generated by Django 2.1.3 on 2019-02-20 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0025_event_action'),
    ]

    operations = [
        migrations.AddField(
            model_name='point',
            name='players',
            field=models.ManyToManyField(related_name='players_on_field', to='db_output.Player'),
        ),
    ]