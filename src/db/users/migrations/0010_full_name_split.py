# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def function(apps, schema_editor):
    OrganizationUser = apps.get_model('users', 'OrganizationUser')  # change this
    for user in OrganizationUser.objects.all():
        names = user.first_name.split()
        user.first_name = names[0]
        user.surnames = ' '.join(names[1:])
        user.save()

    StaffUser = apps.get_model('users', 'StaffUser')  # change this
    for user in StaffUser.objects.all():
        names = user.first_name.split()
        user.first_name = names[0]
        user.surnames = ' '.join(names[1:])
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_auto_20180321_1612'),  # change this
    ]

    operations = [
        migrations.RunPython(function),
    ]
