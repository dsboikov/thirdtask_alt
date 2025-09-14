from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # при сохранении пользователя ничего не меняем в профиле автоматически
        pass
