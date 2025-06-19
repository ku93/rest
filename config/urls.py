from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = ([
    path("admin/", admin.site.urls),
    path("", include("attendance.urls", namespace="attendance")),
    path("restaurant/", include("persons.urls", namespace="persons")),
    path("users/", include("users.urls", namespace="users")),
    path("tables/", include("tables.urls", namespace="tables")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("booking/", include("booking.urls", namespace="booking")),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
