# Generated by Django 5.1.2 on 2024-10-23 06:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_alter_order_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='user_last_update',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='last_update', to=settings.AUTH_USER_MODEL),
        ),
    ]
