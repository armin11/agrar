# Generated by Django 4.2.16 on 2024-09-30 05:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('farmshop', '0013_package_shop_quota'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='package',
            name='shop_quota',
        ),
        migrations.AddField(
            model_name='inventory',
            name='online_quota',
            field=models.IntegerField(default=0, help_text='Maximal online bestellbare Menge', verbose_name='Online Kontingent'),
        ),
    ]
