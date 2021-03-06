# Generated by Django 2.1.3 on 2019-01-25 21:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0021_csvdocument_season'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='game',
            options={'ordering': ('datetime',)},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ('team_name',)},
        ),
        migrations.AlterField(
            model_name='game',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='this_team', to='db_output.Team'),
        ),
    ]
