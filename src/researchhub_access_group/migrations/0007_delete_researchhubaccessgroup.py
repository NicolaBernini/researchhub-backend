# Generated by Django 2.2 on 2021-10-07 00:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0068_remove_organization_access_group'),
        ('researchhub_document', '0025_auto_20211007_0017'),
        ('researchhub_access_group', '0006_remove_permission_access_group'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ResearchhubAccessGroup',
        ),
    ]
