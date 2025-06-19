from django.contrib import admin

from attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Услуги админка"""

    list_display = (
        "id",
        "name",
        "is_active",
    )
    list_filter = (
        "id",
        "name",
        "is_active",
    )
    search_fields = ("name",)
