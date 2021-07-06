# Generated by Django 3.2.3 on 2021-07-01 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_name', '0007_user_getemails'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='getEmails',
            new_name='receive_contact',
        ),
        migrations.AddField(
            model_name='user',
            name='contact',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='display_name',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='line_access_token',
            field=models.CharField(default='', max_length=300),
        ),
    ]
