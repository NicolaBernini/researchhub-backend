# Generated by Django 2.2 on 2022-01-29 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researchhub_document', '0027_rscexchangerate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rscexchangerate',
            name='target_currency',
            field=models.CharField(choices=[('USD', 'USD'), ('ETHER', 'ETHER')], db_index=True, max_length=255),
        ),
    ]
