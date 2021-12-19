# Generated by Django 4.0 on 2021-12-17 04:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_name', '0051_remove_event_random_seed1_remove_event_random_seed2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='rand_latitude',
            field=models.DecimalField(blank=True, decimal_places=20, default=0, max_digits=23),
        ),
        migrations.AddField(
            model_name='event',
            name='rand_longitude',
            field=models.DecimalField(blank=True, decimal_places=20, default=0, max_digits=23),
        ),
        migrations.AlterField(
            model_name='event',
            name='date_time',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 12, 17, 13, 43, 30, 603774)),
        ),
    ]
