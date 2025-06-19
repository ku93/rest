from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Бронь админка"""

    list_display = ("user", "table", "date", "time", "duration", "created_at")
    list_filter = ("date", "table")
    search_fields = ("user__username",)
