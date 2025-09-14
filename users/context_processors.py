from orders.services.cart import Cart

def cart_items_count(request):
    """
    Контекстный процессор: добавляет количество товаров в корзине
    в контекст всех шаблонов.
    """
    if request.session.get('cart'):
        cart = Cart(request)
        return {'cart_items_count': len(cart)}
    return {'cart_items_count': 0}