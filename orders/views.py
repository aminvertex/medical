from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Order
from .services import get_cart


@login_required
def cart_page(request):
    cart = get_cart(request.user)
    items = cart.items.select_related("course", "course__category")
    subtotal = sum(item.course.price for item in items)
    return render(request, "orders/cart.html", {"cart": cart, "cart_items": items, "subtotal": subtotal})


@login_required
def checkout_page(request):
    cart = get_cart(request.user)
    items = list(cart.items.select_related("course"))
    if not items:
        return redirect("cart")
    subtotal = sum(item.course.price for item in items)
    return render(request, "orders/checkout.html", {"cart_items": items, "subtotal": subtotal})


@login_required
def payment_success(request, order_number):
    orders = Order.objects.select_related("payment").prefetch_related("items")
    if not request.user.is_admin_role:
        orders = orders.filter(user=request.user)
    order = get_object_or_404(orders, number=order_number)
    if order.status != Order.Status.PAID:
        return redirect("my_orders")
    return render(request, "orders/success.html", {"order": order})
