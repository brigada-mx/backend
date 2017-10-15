# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClientUserToken',
            fields=[
                ('key', models.CharField(serialize=False, max_length=40, verbose_name='Key', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
            ],
            options={
                'verbose_name_plural': 'Client Tokens',
                'verbose_name': 'Client Token',
            },
        ),
        migrations.CreateModel(
            name='NurseUserToken',
            fields=[
                ('key', models.CharField(serialize=False, max_length=40, verbose_name='Key', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
            ],
            options={
                'verbose_name_plural': 'Nurse Tokens',
                'verbose_name': 'Nurse Token',
            },
        ),
    ]
