from __future__ import annotations
from typing import Any
import graphene
from graphene_django import DjangoObjectType
from django.db.models import Sum
from orders.models import Order, OrderItem
from products.models import Product


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "status", "total_price", "created_at")


class AnalyticsType(graphene.ObjectType):
    total_revenue = graphene.Float()
    orders_count = graphene.Int()
    avg_check = graphene.Float()
    top_products = graphene.List(ProductType)


class Query(graphene.ObjectType):
    analytics = graphene.Field(AnalyticsType)

    def resolve_analytics(self, info: Any) -> AnalyticsType:
        qs = Order.objects.filter(status__in=["paid", "shipped", "delivered"])
        total = qs.aggregate(s=Sum("total_price"))["s"] or 0
        cnt = qs.count()
        avg = float(total) / cnt if cnt else 0.0
        top = Product.objects.annotate(sold=Sum("orderitem__quantity")).order_by("-sold")[:5]
        return AnalyticsType(
            total_revenue=float(total),
            orders_count=cnt,
            avg_check=avg,
            top_products=top,
        )


schema = graphene.Schema(query=Query)
