from __future__ import annotations

from decimal import Decimal
from typing import Iterator, Dict, Any
from django.http import HttpRequest
from products.models import Product

CART_SESSION_ID = "cart"


class Cart:
    def __init__(self, request: HttpRequest) -> None:
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart: dict[str, dict[str, str | int]] = cart

    def add(self, product: Product, quantity: int = 1, override: bool = False) -> None:
        pid = str(product.id)
        if pid not in self.cart:
            self.cart[pid] = {"quantity": 0, "price": str(product.price)}
        if override:
            self.cart[pid]["quantity"] = quantity
        else:
            self.cart[pid]["quantity"] = int(self.cart[pid]["quantity"]) + quantity
        self.save()

    def remove(self, product: Product) -> None:
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self) -> None:
        self.session[CART_SESSION_ID] = {}
        self.session.modified = True

    def save(self) -> None:
        self.session[CART_SESSION_ID] = self.cart
        self.session.modified = True

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        pids = self.cart.keys()
        products = Product.objects.filter(id__in=pids)
        products_map = {str(p.id): p for p in products}
        for pid, item in self.cart.items():
            product = products_map.get(pid)
            if not product:
                continue
            price = Decimal(item["price"])
            quantity = int(item["quantity"])
            yield {
                "product": product,
                "price": price,
                "quantity": quantity,
                "total_price": price * quantity,
            }

    def __len__(self) -> int:
        return sum(int(item["quantity"]) for item in self.cart.values())

    def get_total_price(self) -> Decimal:
        return sum((item["total_price"] for item in self), Decimal("0.00"))

    def to_dict(self) -> dict:
        return {
            "items": [
                {
                    "product_id": item["product"].id,
                    "name": item["product"].name,
                    "price": str(item["price"]),
                    "quantity": item["quantity"],
                    "total": str(item["total_price"]),
                }
                for item in self
            ],
            "total": str(self.get_total_price()),
        }
