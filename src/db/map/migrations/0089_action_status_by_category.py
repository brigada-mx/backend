# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-06-27 18:56
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0088_volunteeropportunity_preview'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='status_by_category',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, help_text='For caching transparency score information'),
        ),
    ]
