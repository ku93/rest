from django.contrib import admin

from persons.models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Сотрудники админка"""

    list_display = (
        "id",
        "name",
        "post",
        "is_active",
    )
    list_filter = (
        "id",
        "name",
        "post",
        "is_active",
    )
    search_fields = (
        "name",
        "post",
        "is_active",
    )
