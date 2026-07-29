def global_store_context(request):
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart_count = request.user.cart.items.count()
        except Exception:
            cart_count = 0
    return {"global_cart_count": cart_count}
