# Generated by Django 4.2.6 on 2024-04-18 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0006_rename_variation_cartitem_variations'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='order_total',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
