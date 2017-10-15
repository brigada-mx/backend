# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('nurses', '0001_initial'),
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='nurseusertoken',
            name='user',
            field=models.OneToOneField(related_name='nurse_auth_token', to='nurses.NurseUser'),
        ),
        migrations.AddField(
            model_name='clientusertoken',
            name='user',
            field=models.OneToOneField(related_name='client_auth_token', to='clients.ClientUser'),
        ),
    ]
