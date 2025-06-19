from django.conf.urls.static import static
from django.urls import path

from attendance.apps import AttendanceConfig
from attendance.views import (AttendanceCreateView, AttendanceDeleteView,
                              AttendanceDetailView, AttendanceUpdateView,
                              index)
from config import settings

app_name = AttendanceConfig.name

urlpatterns = [
    path("", index, name="index"),
    path("attendance/<int:pk>/", AttendanceDetailView.as_view(), name="attendance-detail"),
    path("attendance_create/", AttendanceCreateView.as_view(), name="attendance_create"),
    path(
        "attendance/<int:pk>/update/",
        AttendanceUpdateView.as_view(),
        name="attendance_update",
    ),
    path(
        "attendance/<int:pk>/delete/",
        AttendanceDeleteView.as_view(),
        name="attendance_delete",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
