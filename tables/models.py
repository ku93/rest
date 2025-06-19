from datetime import datetime, timedelta
from typing import Dict, List

from django.db import models
from django.utils import timezone

from booking.models import Booking


class Table(models.Model):
    """
    Модель столиков ресторана или кафе.
    Атрибуты:
        name (CharField): Название столика.
        description (TextField): Описание столика.
        numbers (PositiveIntegerField): Уникальный номер столика.
        number_of_seats (PositiveIntegerField): Количество посадочных мест за столиком.
        location (CharField): Место расположения столика.
        picture (ImageField): Фото столика, загружается в папку 'tables/'.
        is_active (BooleanField): Флаг активности столика (отображается ли столик).
        created_at (DateTimeField): Дата и время создания записи.
        updated_at (DateTimeField): Дата и время последнего обновления записи.
    Методы:
        get_availability_statuses(date, slot_times, slot_duration):
            Для заданной даты и списка слотов с указанной длительностью возвращает словарь статусов каждого слота.
            Статусы:
                - 'free' — свободен
                - 'booked' — забронирован (в будущем)
                - 'occupied' — занят в текущий момент
    Метаданные:
        verbose_name: Читаемое название модели в единственном числе.
        verbose_name_plural: Читаемое название модели во множественном числе.
        ordering: Сортировка по номеру столика.
        permissions: Дополнительные права для управления бронированиями.
    """

    name = models.CharField(max_length=100, verbose_name="Название столика")
    description = models.TextField(verbose_name="Описание столика")
    numbers = models.PositiveIntegerField(unique=True, verbose_name="Номер столика")
    number_of_seats = models.PositiveIntegerField(verbose_name="Количество посадочных мест")
    location = models.CharField(verbose_name="Место расположение", max_length=100)
    picture = models.ImageField(verbose_name="Фото столика", upload_to="tables/")
    is_active = models.BooleanField(verbose_name="Активен", default=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Дата обновления", auto_now=True)

    def get_availability_statuses(
        self, date: datetime.date, slot_times: List[datetime.time], slot_duration: timedelta
    ) -> Dict[datetime.time, str]:
        """
        Возвращает статусы занятости столика для каждого временного слота на указанную дату.
        Аргументы:
            date (datetime.date): Дата для проверки.
            slot_times (List[datetime.time]): Список времен начала временных слотов (например, 10:00, 11:00 и т.п.).
            slot_duration (timedelta): Длительность одного временного слота.
        Возвращает:
            Dict[datetime.time, str]: Словарь, где ключ — время слота, значение — статус:
                'free' — свободен,
                'booked' — забронирован (но не сейчас),
                'occupied' — занят в текущий момент.
        Логика:
            - Получает все активные бронирования столика на указанную дату.
            - Для каждого слота проверяет пересечение с бронированиями.
            - Если слот пересекается с бронированием, и текущее время внутри интервала бронирования — статус 'occupied'
            - Если пересекается, но текущее время вне интервала — 'booked'.
            - Иначе — 'free'.
        """
        now = timezone.localtime()
        today = now.date()
        statuses = {}

        bookings = Booking.objects.filter(table=self, date=date, status="ACTIVE")

        for slot_time in slot_times:
            slot_start = timezone.make_aware(datetime.combine(date, slot_time))
            slot_end = slot_start + slot_duration

            status = "free"
            for booking in bookings:
                booking_start = timezone.make_aware(datetime.combine(booking.date, booking.time))
                booking_end = booking_start + timedelta(hours=booking.duration)

                if booking_start < slot_end and booking_end > slot_start:
                    if date == today and booking_start <= now < booking_end:
                        status = "occupied"
                    else:
                        status = "booked"
                    break

            statuses[slot_time] = status

        return statuses

    class Meta:
        verbose_name = "Столик"
        verbose_name_plural = "Столики"
        ordering = ["numbers"]
        permissions = [
            ("can_reserve", "Может создавать бронь"),
            ("can_cancel_reservation", "Может отменять бронь"),
            ("can_change_reservation", "Может изменять бронь"),
        ]

    def __str__(self):
        """
        Возвращает строковое представление объекта — название столика.
        """
        return self.name
