# Generated by Django 4.0 on 2022-01-25 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_name', '0072_rename_postal_code_event_area'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='attending_limit',
            field=models.IntegerField(default=999999),
        ),
    ]
