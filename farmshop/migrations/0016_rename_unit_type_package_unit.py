# Generated by Django 4.2.16 on 2024-09-30 06:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('farmshop', '0015_package_unit_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='package',
            old_name='unit_type',
            new_name='unit',
        ),
    ]
