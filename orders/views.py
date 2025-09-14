from __future__ import annotations
from typing import Any, cast
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpRequest, HttpResponse
from django.db.models import QuerySet

from rest_framework import viewsets, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action

from .forms import CheckoutForm
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from .services.cart import Cart
from products.models import Product


# Web views

def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get("quantity", 1))
    if quantity < 1:
        messages.error(request, "Количество должно быть >= 1.")
        return redirect(product.get_absolute_url())
    if product.stock < quantity:
        messages.error(request, "Недостаточно товара на складе.")
        return redirect(product.get_absolute_url())
    cart.add(product, quantity)
    messages.success(request, "Товар добавлен в корзину.")
    return redirect("orders:cart_detail")


def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, "Товар удален из корзины.")
    return redirect("orders:cart_detail")


@login_required
def checkout(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Корзина пуста.")
        return redirect("products:product_list")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            serializer = OrderCreateSerializer(data=form.cleaned_data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            order = serializer.save()
            messages.success(request, f"Заказ #{order.id} создан. Спасибо!")
            return redirect("users:account")
    else:
        form = CheckoutForm()
    return render(request, "checkout/checkout.html", {"cart": cart, "form": form})


# REST API

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: Any, obj: Order) -> bool:
        return obj.user == request.user


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self) -> QuerySet[Order]:
        user: User = cast(User, self.request.user)  # IsAuthenticated гарантирует User
        return Order.objects.filter(user=user).prefetch_related("items__product")

    def get_serializer_class(self) -> type[OrderCreateSerializer | OrderSerializer]:
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["patch"])
    def cancel(self, request: Request, pk: int | str | None = None) -> Response:
        order = self.get_object()
        if order.status in ["shipped", "delivered"]:
            return Response({"detail": "Нельзя отменить отправленный/доставленный заказ."}, status=400)
        order.status = "cancelled"
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order).data)
