from __future__ import annotations
from typing import List, Union
from django.urls import path, include, URLPattern, URLResolver
from rest_framework.routers import DefaultRouter
from .views import (
    ProductListView, ProductDetailView, add_review,
    ProductViewSet, CategoryViewSet, CartApiViewSet,
    CategoryListView, CategoryDetailView,
)


app_name = "products"


# Web
urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("products/", ProductListView.as_view(), name="product_list"),
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("category/<slug:slug>/", CategoryDetailView.as_view(), name="category_detail"),
    path("product/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path("product/<slug:slug>/review/", add_review, name="add_review"),
]

# API
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="api-products")
router.register(r"categories", CategoryViewSet, basename="api-categories")
router.register(r"cart", CartApiViewSet, basename="api-cart")

api_urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("", include(router.urls)),
]

urlpatterns += [
    path("api/", include((api_urlpatterns, "products"), namespace="api-products")),
]
