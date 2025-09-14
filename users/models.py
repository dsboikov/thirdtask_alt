from __future__ import annotations
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message="Телефон должен быть в формате +71234567890 или 10–15 цифр."
)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")  #type=User
    full_name = models.CharField("ФИО", max_length=255, blank=True)  #type=CharField
    phone = models.CharField("Телефон",
                             max_length=16, blank=True, validators=[phone_validator])  #type=CharField

    def __str__(self) -> str:
        return f"Профиль {self.user.username}"
