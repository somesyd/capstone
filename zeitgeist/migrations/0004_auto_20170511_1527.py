# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-11 15:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zeitgeist', '0003_auto_20170510_1909'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchquery',
            name='latitude',
            field=models.FloatField(default=None),
        ),
        migrations.AddField(
            model_name='searchquery',
            name='longitude',
            field=models.FloatField(default=None),
        ),
    ]