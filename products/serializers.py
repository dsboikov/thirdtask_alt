from __future__ import annotations
from rest_framework import serializers
from .models import Category, Product, Review


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent"]


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "comment", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "price", "category",
            "image", "is_active", "stock", "created_at", "updated_at", "average_rating"
        ]


class ProductCreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def validate(self, attrs):
        request = self.context["request"]
        product: Product = self.context["product"]
        user = request.user
        # Проверка: отзыв только после покупки (есть OrderItem у пользователя)
        from orders.models import Order, OrderItem
        has_bought = Order.objects.filter(
            user=user,
            items__product=product,
        ).exclude(status="cancelled").exists()
        if not has_bought:
            raise serializers.ValidationError("Вы можете оставить отзыв только после покупки товара.")
        return attrs

    def create(self, validated_data):
        product: Product = self.context["product"]
        user = self.context["request"].user
        return Review.objects.create(product=product, user=user, **validated_data)
