from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from booking.models import Booking


@shared_task
def send_booking_confirmation(booking_id):
    """Отправка подтверждения бронирования"""
    from booking.models import Booking

    booking = Booking.objects.get(pk=booking_id)

    user_subject = f"Подтверждение бронирования столика №{booking.table.numbers}"
    user_message = f"""
Подтверждение вашего бронирования

Детали брони:
Номер стола: {booking.table.numbers}
Название: {booking.table.name}
Дата: {booking.date.strftime('%d.%m.%Y')}
Время: {booking.time.strftime('%H:%M')}
Продолжительность: {booking.duration} часа(ов)
Количество гостей: {booking.person_count}

Спасибо за выбор нашего заведения!
"""
    send_mail(user_subject, user_message, settings.EMAIL_HOST_USER, [booking.user.email], fail_silently=False)

    admin_subject = f"Новое бронирование столика №{booking.table.numbers}"
    admin_message = f"""
Новое бронирование #{booking.id}

Детали:
Стол: №{booking.table.numbers} ({booking.table.name})
Дата/время: {booking.date.strftime('%d.%m.%Y')} в {booking.time.strftime('%H:%M')}
Гости: {booking.person_count} человек
Клиент: {booking.user.get_full_name()}
Email: {booking.user.email}
"""
    send_mail(admin_subject, admin_message, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=False)


@shared_task
def send_booking_update(booking_id, old_date, old_time):
    """Отправка уведомления об изменении брони"""

    booking = Booking.objects.get(pk=booking_id)
    subject = "Изменение бронирования #"
    message = f"""
Изменение бронирования #

Было:
Дата/время: {old_date.strftime('%d.%m.%Y')} в {old_time.strftime('%H:%M')}

Новые данные:
Стол: №{booking.table.numbers} ({booking.table.name})
Дата/время: {booking.date.strftime('%d.%m.%Y')} в {booking.time.strftime('%H:%M')}
"""
    send_mail(
        subject, message, settings.EMAIL_HOST_USER, [booking.user.email, settings.EMAIL_HOST_USER], fail_silently=False
    )


@shared_task
def send_booking_cancellation(booking_id):
    """Отправка уведомления об отмене брони"""

    booking = Booking.objects.get(pk=booking_id)
    subject = "Отмена бронирования #"
    message = f"""
Отмена бронирования #

Детали отменённого брони:
Стол: №{booking.table.numbers} ({booking.table.name})
Дата: {booking.date.strftime('%d.%m.%Y')}
Время: {booking.time.strftime('%H:%M')}
"""
    send_mail(
        subject, message, settings.EMAIL_HOST_USER, [booking.user.email, settings.EMAIL_HOST_USER], fail_silently=False
    )


def check_booking_endtimes():
    """Простая проверка завершённых бронирований"""
    active_bookings = Booking.objects.filter(status="ACTIVE")

    for booking in active_bookings:
        end_time = timezone.make_aware(datetime.combine(booking.date, booking.time)) + timedelta(
            hours=booking.duration
        )

        if timezone.now() >= end_time:
            booking.status = "COMPLETED"
            booking.save(update_fields=["status"])

    return redirect(f"{reverse('users:profile')}?tab=booking_history")
