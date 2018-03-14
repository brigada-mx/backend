# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def function(apps, schema_editor):
    Submission = apps.get_model('map', 'Submission')  # change this
    for s in Submission.objects.all():
        images = []
        for url in s.image_urls:
            images.append({'url': url})
        s.image_urls = images
        s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0053_auto_20180313_1328'),  # change this
    ]

    operations = [
        migrations.RunPython(function),
    ]
