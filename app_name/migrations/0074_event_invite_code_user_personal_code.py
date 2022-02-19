# Generated by Django 4.0 on 2022-02-19 02:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_name', '0073_alter_event_attending_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='invite_code',
            field=models.CharField(blank=True, default='', max_length=40),
        ),
        migrations.AddField(
            model_name='user',
            name='personal_code',
            field=models.CharField(blank=True, default='', max_length=40),
        ),
    ]
