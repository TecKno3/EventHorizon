# Generated by Django 4.0 on 2021-12-26 10:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_name', '0058_remove_image_event_id_event_images_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='date_time',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 12, 26, 19, 27, 39, 551892)),
        ),
    ]
