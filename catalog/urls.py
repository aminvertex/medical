from django.urls import path
from . import views

urlpatterns = [
    path("shop/", views.shop, name="shop"),
    path("courses/<slug:slug>/", views.course_detail, name="course_detail"),
]
