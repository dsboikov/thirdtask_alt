from __future__ import annotations
from typing import Any, Type
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_profile(sender: Type[User], instance: User, created: bool, **kwargs: Any) -> None:
    if created:
        Profile.objects.create(user=instance)
