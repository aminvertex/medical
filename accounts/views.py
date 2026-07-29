from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from orders.models import Enrollment, Order
from catalog.models import Favorite


@ensure_csrf_cookie
def auth_page(request):
    if request.user.is_authenticated:
        return redirect("account_overview")
    return render(request, "accounts/auth.html")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def account_overview(request):
    context = {
        "orders_count": Order.objects.filter(user=request.user).count(),
        "courses_count": Enrollment.objects.filter(user=request.user, is_active=True).count(),
        "favorites_count": Favorite.objects.filter(user=request.user).count(),
        "recent_orders": Order.objects.filter(user=request.user).prefetch_related("items")[:5],
    }
    return render(request, "accounts/account.html", context)


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items", "payment")
    return render(request, "accounts/my_orders.html", {"orders": orders})


@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(user=request.user, is_active=True).select_related("course", "order_item")
    return render(request, "accounts/my_courses.html", {"enrollments": enrollments})


@login_required
def my_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related("course", "course__category")
    return render(request, "accounts/my_favorites.html", {"favorites": favorites})
