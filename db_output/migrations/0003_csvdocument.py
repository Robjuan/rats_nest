# Generated by Django 2.1.3 on 2018-11-30 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_output', '0002_auto_20181128_2312'),
    ]

    operations = [
        migrations.CreateModel(
            name='csvDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=255)),
                ('document', models.FileField(upload_to='csv/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
