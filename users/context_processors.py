from __future__ import annotations
from typing import Any
from django.http import HttpRequest
from orders.services.cart import Cart


def cart(request: HttpRequest) -> dict[str, Any]:
    return {"cart_items_count": len(Cart(request))}

