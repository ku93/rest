from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
    )
    list_filter = ("email",)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.groups.filter(name="Менеджер").exists():
            if request.user.groups.filter(name="Менеджер").exists():
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.groups.filter(name="Менеджер").exists():
            if request.user.groups.filter(name="Менеджер").exists():
                return False
        return super().has_delete_permission(request, obj)
