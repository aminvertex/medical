from django.urls import path
from . import views

urlpatterns = [
    path("auth/", views.auth_page, name="auth_page"),
    path("logout/", views.logout_view, name="logout"),
    path("account/", views.account_overview, name="account_overview"),
    path("account/orders/", views.my_orders, name="my_orders"),
    path("account/courses/", views.my_courses, name="my_courses"),
    path("account/favorites/", views.my_favorites, name="my_favorites"),
]
