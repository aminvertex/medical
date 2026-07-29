from django.urls import path
from . import views

urlpatterns = [
    path("cart/", views.cart_page, name="cart"),
    path("checkout/", views.checkout_page, name="checkout"),
    path("checkout/success/<str:order_number>/", views.payment_success, name="payment_success"),
]
