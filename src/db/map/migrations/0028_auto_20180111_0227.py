# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-11 02:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0027_auto_20180111_0148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='key',
            field=models.IntegerField(help_text='Essentially google sheet row number'),
        ),
    ]