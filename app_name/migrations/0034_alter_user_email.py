# Generated by Django 3.2.3 on 2021-07-12 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_name', '0033_alter_user_alerts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.CharField(blank=True, max_length=40, unique=True),
        ),
    ]
