from .services.cart import Cart


def cart(request):
    return {"cart_items_count": len(Cart(request))}
