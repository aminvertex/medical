from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from config.api import api

urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(
            url="/static/assets/logonomy-1763455510995.png",
            permanent=False,
        ),
        name="favicon",
    ),
    path("django-admin/", admin.site.urls),
    path("api/", api.urls),
    path("", include("core.urls")),
    path("", include("accounts.urls")),
    path("", include("catalog.urls")),
    path("", include("orders.urls")),
    path("", include("dashboard.urls")),
]

handler403 = "core.views.permission_denied_view"
handler404 = "core.views.page_not_found_view"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
