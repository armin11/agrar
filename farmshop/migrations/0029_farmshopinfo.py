# Generated by Django 4.2.16 on 2024-10-19 12:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import farmshop.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('farmshop', '0028_postaladdress_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='FarmShopInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generic_id', models.UUIDField(default=uuid.uuid4)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('changed', models.DateTimeField(blank=True, null=True)),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('active', models.BooleanField(blank=True, default=True)),
                ('title', models.CharField(max_length=300, verbose_name='Titel')),
                ('description', models.CharField(blank=True, max_length=4096, null=True, verbose_name='Beschreibung')),
                ('image', models.ImageField(blank=True, help_text='Beispielbild', null=True, upload_to=farmshop.models.FarmShopInfo.get_upload_path, verbose_name='Bild')),
                ('farmshop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='farmshop.farmshop')),
                ('owned_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
