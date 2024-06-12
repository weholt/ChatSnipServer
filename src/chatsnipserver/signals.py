from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ChatSnipProfile


@receiver(post_save, sender=get_user_model())
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        ChatSnipProfile.objects.create(user=instance)
    else:
        if not hasattr(instance, "chatsnipprofile"):
            ChatSnipProfile.objects.create(user=instance)
        else:
            instance.chatsnipprofile.save()
