from django.db import models

from users.models import User


class Attendance(models.Model):
    """Модель услуг ресторана"""

    name = models.CharField(max_length=50, verbose_name="Наименование услуги")
    description = models.TextField(verbose_name="Описание услуги")
    price = models.PositiveIntegerField(null=True, blank=True, verbose_name="Цена")
    image = models.ImageField(upload_to="attendance", verbose_name="Изображение", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

        permissions = [
            ("can_add_attendance", "Может добавлять услуги"),
            ("can_change_attendance", "Может изменять услуги"),
            ("can_delete_attendance", "Может удалять услуги"),
        ]

    def __str__(self):
        return self.name
