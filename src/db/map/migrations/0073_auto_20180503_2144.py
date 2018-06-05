# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-03 21:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0072_discoursetopicevent_discourse_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='source',
            field=models.TextField(choices=[('kobo', 'KoBo'), ('brigada', 'Brigada')]),
        ),
        migrations.AlterField(
            model_name='submission',
            name='source_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]