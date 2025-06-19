from django.contrib import admin

from tables.models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    """Админка столиков"""

    list_display = ("numbers", "name", "location")
    list_filter = ("numbers", "name", "location")
    search_fields = ("name", "location")
