from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction

from products.models import Product


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


ORDER_STATUS_CHOICES = [
    ("pending", "Ожидает оплаты"),
    ("paid", "Оплачен"),
    ("shipped", "Отправлен"),
    ("delivered", "Доставлен"),
    ("cancelled", "Отменен"),
]


class Order(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_address = models.TextField()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self) -> str:
        return f"Order #{self.pk} — {self.user} — {self.status}"

    @transaction.atomic
    def recalc_total(self) -> None:
        total = sum((item.price * item.quantity for item in self.items.select_related("product")), Decimal("0.00"))
        self.total_price = total
        self.save(update_fields=["total_price"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="+", on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot price

    class Meta:
        unique_together = ("order", "product")
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self) -> str:
        return f"{self.product} x {self.quantity}"
