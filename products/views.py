from __future__ import annotations

from typing import Any, List
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, DetailView
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product, Category, Review, ProductView
from .filters import ProductFilter
from .forms import ReviewForm
from .serializers import (
    ProductSerializer, CategorySerializer, ReviewSerializer, ProductCreateReviewSerializer
)
from orders.services.cart import Cart


# Хэлпер для потомков категории
def get_descendant_ids(root: Category) -> list[int]:
    ids: List[int] = [root.id]
    level = [root.id]
    while level:
        children = Category.objects.filter(parent_id__in=level).values_list("id", flat=True)
        children = list(children)
        if not children:
            break
        ids.extend(children)
        level = children
    return ids


# Въюхи
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
        # Фильтры (включая category/id и category_slug)
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
            qs = qs.annotate(cnt=Count("reviews")).order_by("-cnt")
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all().order_by("name")
        selected = self.request.GET.get("category")
        ctx["selected_category_id"] = int(selected) if selected and selected.isdigit() else None
        ctx["current_category"] = None  # для совместимости с шаблоном
        return ctx


class HomeView(ProductListView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        N = 12
        with_img = Product.objects.filter(is_active=True, image__isnull=False).order_by("-created_at")[:N]
        remain = N - with_img.count()
        if remain > 0:
            without_img = Product.objects.filter(is_active=True, image__isnull=True).order_by("-created_at")[:remain]
        else:
            without_img = Product.objects.none()
        ctx["slider_products"] = list(with_img) + list(without_img)
        return ctx


class CategoryListView(ListView):
    template_name = "products/category_list.html"
    model = Category
    context_object_name = "categories"

    def get_queryset(self):
        # Топ-уровень с prefetch детей (1 уровень для простоты)
        return Category.objects.filter(parent__isnull=True).prefetch_related("children").order_by("name")


class CategoryDetailView(ProductListView):
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        ids = get_descendant_ids(self.category)
        base = Product.objects.select_related("category").filter(is_active=True, category_id__in=ids)
        # Применяем остальные фильтры/поиск/сортировку поверх базового
        f = ProductFilter(self.request.GET, queryset=base)
        qs = f.qs
        ordering = self.request.GET.get("ordering")
        if ordering == "price":
            qs = qs.order_by("price")
        elif ordering == "-price":
            qs = qs.order_by("-price")
        elif ordering == "new":
            qs = qs.order_by("-created_at")
        elif ordering == "popular":
            qs = qs.annotate(cnt=Count("reviews")).order_by("-cnt")
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["current_category"] = self.category
        ctx["categories"] = Category.objects.all().order_by("name")
        ctx["selected_category_id"] = self.category.id
        return ctx


class ProductDetailView(DetailView):
    template_name = "products/product_detail.html"
    model = Product
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._record_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["reviews"] = self.object.reviews.select_related("user")
        ctx["form"] = ReviewForm()
        ctx["back_url"] = self.request.META.get("HTTP_REFERER") or reverse("products:product_list")
        return ctx

    def _record_view(self, request, product: Product) -> None:
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key or ""
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
        user = request.user if request.user.is_authenticated else None
        Product.objects.filter(pk=product.pk).update(view_count=F("view_count") + 1)
        ProductView.objects.create(product=product, user=user, session_key=session_key, ip=ip)


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
