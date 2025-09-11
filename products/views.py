from __future__ import annotations

from typing import Any
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product, Category, Review
from .filters import ProductFilter
from .forms import ReviewForm
from .serializers import (
    ProductSerializer, CategorySerializer, ReviewSerializer, ProductCreateReviewSerializer
)
from orders.services.cart import Cart


# Web views

class ProductListView(ListView):
    template_name = "products/product_list.html"
    model = Product
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.select_related("category").filter(is_active=True)
        # Поиск
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        # Фильтры
        f = ProductFilter(self.request.GET, queryset=qs)
        qs = f.qs
        # Сортировка
        ordering = self.request.GET.get("ordering")
        if ordering == "price":
            qs = qs.order_by("price")
        elif ordering == "-price":
            qs = qs.order_by("-price")
        elif ordering == "new":
            qs = qs.order_by("-created_at")
        elif ordering == "popular":
            qs = qs.annotate(cnt=models.Count("reviews")).order_by("-cnt")
        return qs


class ProductDetailView(DetailView):
    template_name = "products/product_detail.html"
    model = Product
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "product"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["reviews"] = self.object.reviews.select_related("user")
        ctx["form"] = ReviewForm()
        return ctx


@login_required
def add_review(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug, is_active=True)
    form = ReviewForm(request.POST)
    if form.is_valid():
        # Бизнес-правило: отзыв только после покупки
        from orders.models import Order
        has_bought = Order.objects.filter(user=request.user, items__product=product).exclude(
            status="cancelled").exists()
        if not has_bought:
            messages.error(request, "Оставлять отзыв можно только после покупки.")
            return redirect(product.get_absolute_url())
        Review.objects.update_or_create(
            product=product, user=request.user,
            defaults=form.cleaned_data
        )
        messages.success(request, "Спасибо! Ваш отзыв сохранен.")
    else:
        messages.error(request, "Исправьте ошибки формы.")
    return redirect(product.get_absolute_url())


# REST API

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.select_related("category").filter(is_active=True)
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated])
    def reviews(self, request, pk=None):
        product = self.get_object()
        if request.method == "GET":
            qs = product.reviews.select_related("user").all()
            return Response(ReviewSerializer(qs, many=True).data)
        serializer = ProductCreateReviewSerializer(
            data=request.data, context={"request": request, "product": product}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class CartApiViewSet(viewsets.ViewSet):
    """
    API для корзины на сессиях.
    """
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        cart = Cart(request)
        return Response(cart.to_dict())

    def create(self, request):
        # POST: {"product_id": 1, "quantity": 2}
        product_id = int(request.data.get("product_id"))
        quantity = int(request.data.get("quantity", 1))
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        Cart(request).add(product=product, quantity=quantity, override=False)
        return Response(Cart(request).to_dict(), status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        # PATCH /api/cart/{product_id}/ {"quantity": 3}
        product = get_object_or_404(Product, pk=pk)
        qty = int(request.data.get("quantity", 1))
        Cart(request).add(product, qty, override=True)
        return Response(Cart(request).to_dict())

    def destroy(self, request, pk=None):
        product = get_object_or_404(Product, pk=pk)
        Cart(request).remove(product)
        return Response(Cart(request).to_dict(), status=status.HTTP_204_NO_CONTENT)
