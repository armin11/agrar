# Generated by Django 4.2.16 on 2024-09-30 04:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('farmshop', '0009_rename_farm_shop_article_farmshop_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='article',
            field=models.ForeignKey(help_text='Hilfe zum Produkt', null=True, on_delete=django.db.models.deletion.CASCADE, to='farmshop.article', verbose_name='Produkt'),
        ),
        migrations.AlterField(
            model_name='package',
            name='description',
            field=models.CharField(max_length=4096, verbose_name='Beschreibung Packung/Paket'),
        ),
        migrations.AlterField(
            model_name='package',
            name='title',
            field=models.CharField(max_length=300, verbose_name='Bezeichnung Packung/Paket'),
        ),
    ]
