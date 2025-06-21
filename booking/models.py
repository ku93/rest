import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    """
    Модель бронирования столика в ресторане.
    Атрибуты:
        user (ForeignKey): пользователь, сделавший бронирование.
        table (ForeignKey): столик, который бронируется.
        date (DateField): дата бронирования.
        time (TimeField): время начала бронирования.
        duration (PositiveIntegerField): длительность бронирования в часах (по умолчанию 1).
        person_count (PositiveIntegerField): количество гостей (по умолчанию 1).
        status (CharField): статус бронирования (активно, отменено, завершено).
        reminder_sent (BooleanField): флаг, отправлено ли напоминание.
        created_at (DateTimeField): дата и время создания записи.
        updated_at (DateTimeField): дата и время последнего обновления записи.
    Метаданные:
        verbose_name: "Бронирование"
        verbose_name_plural: "Бронирования"
        unique_together: уникальность по сочетанию (table, date, time)
        permissions: набор пользовательских прав для управления бронированиями.
    """

    STATUS_CHOICES = [
        ("ACTIVE", "Активно"),
        ("CANCELLED", "Отменено"),
        ("COMPLETED", "Завершено"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    table = models.ForeignKey("tables.Table", on_delete=models.CASCADE, verbose_name="Столик")
    date = models.DateField(verbose_name="Дата бронирования")
    time = models.TimeField(verbose_name="Время бронирования")
    duration = models.PositiveIntegerField(default=1, verbose_name="Длительность (часов)")
    person_count = models.PositiveIntegerField(default=1, verbose_name="Количество персон")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    reminder_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        permissions = [
            ("can_reserve", "Can make a reservation"),
            ("can_view_all_bookings", "Can view all bookings"),
            ("can_change_reservation", "Can change any reservation"),
            ("can_delete_any_booking", "Can delete any booking"),
            ("can_cancel_booking", "Can cancel booking"),
        ]

    def __str__(self):
        """
        Читаемое строковое представление объекта бронирования.
        Формат: "<Столик> - <Дата> <Время> (<Пользователь>)"
        Например: "Столик 5 - 2024-06-20 19:00 (ivan)"
        """
        return f'{self.table} - {self.date} {self.time.strftime("%H:%M")} ({self.user})'

    def clean(self):
        """
        Валидация модели перед сохранением.
        Проверяет:
            - Наличие даты и времени бронирования.
            - Дата бронирования не в прошлом (по локальной дате).
            - Время начала и окончания бронирования попадают в часы работы ресторана:
              * Пн-Пт: с 11:00 до 23:00
              * Сб-Вс: с 10:00 до 23:59
            - Количество гостей не превышает количество мест за столиком.
            - Отсутствие пересечения с существующими бронированиями на тот же столик и дату.
        Выбрасывает:
            ValidationError при нарушении любого из условий.
        """
        if self.date is None:
            raise ValidationError("Дата бронирования обязательна.")

        if self.date < timezone.localdate():
            raise ValidationError("Нельзя бронировать на прошедшую дату.")

        if self.time is None:
            raise ValidationError("Время бронирования обязательно.")

        if self.time < timezone.localtime().time():
            raise ValidationError("Нельзя бронировать на прошедшее время.")

        start_time = self.time
        end_datetime = datetime.datetime.combine(self.date, start_time) + datetime.timedelta(hours=self.duration)
        end_time = end_datetime.time()

        weekday = self.date.weekday()
        if weekday < 5:
            open_time = datetime.time(11, 0)
            close_time = datetime.time(23, 0)
        else:
            open_time = datetime.time(10, 0)
            close_time = datetime.time(23, 59)

        if not (open_time <= start_time < close_time):
            raise ValidationError(
                f"Время начала бронирования должно быть в интервале "
                f"{open_time.strftime('%H:%M')} - {close_time.strftime('%H:%M')}."
            )

        if not (open_time < end_time <= close_time):
            raise ValidationError(
                f"Время окончания бронирования должно быть в интервале "
                f"{open_time.strftime('%H:%M')} - {close_time.strftime('%H:%M')}."
            )

        if self.person_count > self.table.number_of_seats:
            raise ValidationError("Количество человек не может превышать число мест за столом.")

        existing = Booking.objects.filter(table=self.table, date=self.date, status="ACTIVE").exclude(pk=self.pk)
        for b in existing:
            b_start = b.time
            b_end_datetime = datetime.datetime.combine(b.date, b_start) + datetime.timedelta(hours=b.duration)
            b_end = b_end_datetime.time()

            if start_time < b_end and end_time > b_start:
                raise ValidationError(
                    f"Столик уже забронирован на время {b_start.strftime('%H:%M')} - {b_end.strftime('%H:%M')}."
                )
