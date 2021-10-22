# Generated by Django 2.2 on 2021-08-24 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researchhub_document', '0021_auto_20210804_1850'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researchhubpost',
            name='document_type',
            field=models.CharField(choices=[('PAPER', 'PAPER'), ('DISCUSSION', 'DISCUSSION'), ('ELN', 'ELN'), ('HYPOTHESIS', 'HYPOTHESIS'), ('NOTE', 'NOTE')], default='DISCUSSION', max_length=32),
        ),
        migrations.AlterField(
            model_name='researchhubunifieddocument',
            name='document_type',
            field=models.CharField(choices=[('PAPER', 'PAPER'), ('DISCUSSION', 'DISCUSSION'), ('ELN', 'ELN'), ('HYPOTHESIS', 'HYPOTHESIS'), ('NOTE', 'NOTE')], default='PAPER', help_text='Papers are imported from external src. Posts are in-house', max_length=32),
        ),
    ]
