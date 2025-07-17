from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_rename_discount_amount_promo_discount_percent'),
    ]

    operations = [
        migrations.AddField(
            model_name='rental',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rental',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ] 