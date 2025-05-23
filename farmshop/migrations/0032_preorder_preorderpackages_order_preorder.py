# Generated by Django 4.2.16 on 2024-11-01 07:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('farmshop', '0031_farmshopnews_publication_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generic_id', models.UUIDField(default=uuid.uuid4)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('changed', models.DateTimeField(blank=True, null=True)),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('active', models.BooleanField(blank=True, default=True)),
                ('notice', models.CharField(blank=True, max_length=4096, null=True, verbose_name='Anmerkungen')),
                ('start_date', models.DateField(verbose_name='Startdatum')),
                ('end_date', models.DateField(verbose_name='Enddatum')),
                ('farmshop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='farmshop.farmshop')),
                ('owned_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PreOrderPackages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generic_id', models.UUIDField(default=uuid.uuid4)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('changed', models.DateTimeField(blank=True, null=True)),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('active', models.BooleanField(blank=True, default=True)),
                ('max_packages', models.IntegerField(default=1, verbose_name='Maximale Packungen pro Bestellung')),
                ('farmshop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='farmshop.farmshop')),
                ('owned_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='farmshop.package', verbose_name='Packung/Paket')),
                ('preorder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='farmshop.preorder', verbose_name='Vorbestellung')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='order',
            name='preorder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='farmshop.preorder', verbose_name='Vorbestellung'),
        ),
    ]
