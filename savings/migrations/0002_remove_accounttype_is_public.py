# Generated by Django 4.0.4 on 2024-02-01 19:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accounttype',
            name='is_public',
        ),
    ]
