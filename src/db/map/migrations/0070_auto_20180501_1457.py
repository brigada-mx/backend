# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-01 14:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0069_discoursetopicevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='discoursepostevent',
            name='event',
            field=models.TextField(blank=True, db_index=True, help_text='X-Discourse-Event request header'),
        ),
        migrations.AddField(
            model_name='discoursetopicevent',
            name='event',
            field=models.TextField(blank=True, db_index=True, help_text='X-Discourse-Event request header'),
        ),
    ]
