from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Wallet


@receiver(post_save, sender=User)
def create_wallet_for_new_user(sender, instance, created, **kwargs):
    """สร้าง Wallet อัตโนมัติทุกครั้งที่มี User ใหม่"""
    if created:
        Wallet.objects.create(user=instance)