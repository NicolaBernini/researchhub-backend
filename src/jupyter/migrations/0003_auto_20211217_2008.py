# Generated by Django 2.2 on 2021-12-17 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jupyter', '0002_jupytersession_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jupytersession',
            name='uid',
            field=models.CharField(max_length=64),
        ),
    ]
