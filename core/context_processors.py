from orders.models import CartItem


def global_store_context(request):
    """Expose the authenticated user's cart count without hiding DB errors."""

    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(cart__user=request.user).count()
    return {"global_cart_count": cart_count}
