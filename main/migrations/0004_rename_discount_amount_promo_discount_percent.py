from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_alter_car_options_car_last_maintenance_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='promo',
            old_name='discount_amount',
            new_name='discount_percent',
        ),
    ] 