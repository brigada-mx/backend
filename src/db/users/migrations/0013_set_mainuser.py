# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def function(apps, schema_editor):
    OrganizationUser = apps.get_model('users', 'OrganizationUser')  # change this
    for user in OrganizationUser.objects.all():
        user.is_mainuser = True
        user.save()

    DonorUser = apps.get_model('users', 'DonorUser')  # change this
    for user in DonorUser.objects.all():
        user.is_mainuser = True
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_auto_20180405_1412'),  # change this
    ]

    operations = [
        migrations.RunPython(function),
    ]
