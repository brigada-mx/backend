# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-23 00:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0055_auto_20180323_0007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='desc',
            field=models.TextField(blank=True),
        ),
    ]