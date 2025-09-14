from __future__ import annotations
from typing import List, Union
from django.urls import path, include, URLPattern, URLResolver
from rest_framework.routers import DefaultRouter
from .views import cart_detail, cart_add, cart_remove, checkout, OrderViewSet


app_name = "orders"


# Web
urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("cart/", cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", cart_remove, name="cart_remove"),
    path("checkout/", checkout, name="checkout"),
]

# API
router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="api-orders")

api_urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("", include(router.urls)),
]

urlpatterns += [
    path("api/", include((api_urlpatterns, "orders"), namespace="api-orders")),
]
