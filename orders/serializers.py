from __future__ import annotations
from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "total_price", "shipping_address", "created_at", "updated_at", "items"]
        read_only_fields = ["status", "total_price", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        from .services.cart import Cart
        cart = Cart(request)
        if len(cart) == 0:
            raise serializers.ValidationError("Корзина пуста.")
        # Проверка остатков
        for item in cart:
            if item["quantity"] > item["product"].stock:
                raise serializers.ValidationError(f"Недостаточно товара: {item['product'].name}")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        from .services.cart import Cart
        cart = Cart(request)
        order = Order.objects.create(user=user, shipping_address=validated_data["shipping_address"], status="paid")
        # Эмуляция оплаты: статус сразу "paid"
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price=item["price"],
            )
            # списание остатков
            p: Product = item["product"]
            p.stock -= item["quantity"]
            p.save(update_fields=["stock"])
        order.recalc_total()
        cart.clear()
        # email уведомления
        from django.core.mail import send_mail
        send_mail(
            subject=f"Заказ #{order.id} подтвержден",
            message=f"Спасибо за заказ! Сумма: {order.total_price}",
            from_email=None,
            recipient_list=[user.email] if user.email else [],
            fail_silently=True,
        )
        return order
