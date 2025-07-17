from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Client
from datetime import date

@receiver(post_save, sender=User)
def create_client(sender, instance, created, **kwargs):
    if created:
        # Set a default birth date that ensures the user is at least 18 years old
        default_birth_date = date(date.today().year - 18, date.today().month, date.today().day)
        Client.objects.create(
            user=instance,
            birth_date=default_birth_date,
            phone='+375 (29) 000-00-00',  # Default phone number
            address='Please update your address'  # Default address
        )

@receiver(post_save, sender=User)
def save_client(sender, instance, **kwargs):
    instance.client.save() 