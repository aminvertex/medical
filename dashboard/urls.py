from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/users/", views.dashboard_users, name="dashboard_users"),
    path("dashboard/courses/", views.dashboard_courses, name="dashboard_courses"),
    path("dashboard/orders/", views.dashboard_orders, name="dashboard_orders"),
    path("dashboard/messages/", views.dashboard_messages, name="dashboard_messages"),
    path("instructor/", views.instructor_dashboard, name="instructor_dashboard"),
]
