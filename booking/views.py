from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)

from booking.forms import BookingForm
from booking.models import Booking
from booking.tasks import (send_booking_cancellation,
                           send_booking_confirmation, send_booking_update)
from tables.models import Table


class BookingBaseView(LoginRequiredMixin):
    """
    Базовое представление для работы с бронированиями.
    Реализует фильтрацию по пользователю, если у него нет прав на просмотр всех бронирований.
    """

    model = Booking
    context_object_name = "booking"

    def get_queryset(self):
        """
        Возвращает queryset бронирований.
        Если у пользователя нет права 'can_view_all_bookings', возвращает только его бронирования.
        """
        queryset = super().get_queryset()
        if not self.request.user.has_perm("booking.can_view_all_bookings"):
            queryset = queryset.filter(user=self.request.user)
        return queryset


class BookingListView(BookingBaseView, ListView):
    """
    Представление списка бронирований пользователя.
    Отображает активные бронирования и историю (завершённые и отменённые).
    """

    template_name = "users/profile.html"
    paginate_by = 10

    def get_queryset(self):
        """Возвращает активные бронирования текущего пользователя."""
        return Booking.objects.filter(
            user=self.request.user,
            status=Booking.STATUS_CHOICES("ACTIVE"),
        )

    def _mark_completed_bookings(self):
        """
        Помечает прошедшие бронирования как завершённые.
        Проверяет, если текущее время позже окончания бронирования — меняет статус.
        """
        now = timezone.now()
        active_bookings = Booking.objects.filter(user=self.request.user, status=Booking.STATUS_CHOICES("ACTIVE"))
        completed_bookings = []

        for booking in active_bookings:
            booking_end = timezone.make_aware(datetime.combine(booking.date, booking.time)) + timedelta(
                hours=booking.duration
            )

            if now >= booking_end:
                booking.status = Booking.STATUS_CHOICES("COMPLETED")
                booking.save(update_fields=["status"])
                completed_bookings.append(booking)

        return completed_bookings

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст активные бронирования и историю бронирований.
        Также вызывает обновление статусов завершённых бронирований.
        """
        context = super().get_context_data(**kwargs)

        self._mark_completed_bookings()

        bookings = self.get_queryset()
        active_bookings = bookings.filter(status=Booking.STATUS_CHOICES("ACTIVE")).order_by("date", "time")
        booking_history = bookings.filter(
            status__in=[Booking.STATUS_CHOICES("COMPLETED"), Booking.STATUS_CHOICES("CANCELLED")],
        ).order_by("-date", "-time")

        context.update(
            {
                "active_bookings": active_bookings,
                "booking_history": booking_history,
                "tab": self.request.GET.get("tab", "active_bookings"),
            }
        )
        return context


class BookingCreateView(BookingBaseView, CreateView):
    """
    Представление для создания нового бронирования.
    Проверяет права пользователя и передаёт столик в форму.
    """

    permission_required = "booking.can_reserve"
    form_class = BookingForm
    template_name = "booking/booking_form.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Инициализирует выбранный столик, дату и время из параметров запроса.
        """
        self.table = get_object_or_404(Table, numbers=kwargs.get("table_number"))
        self.selected_date = request.GET.get("date")
        self.selected_time = request.GET.get("time")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Передаёт объект столика в форму бронирования."""
        kwargs = super().get_form_kwargs()
        kwargs["table"] = self.table
        return kwargs

    def get_initial(self):
        """
        Устанавливает начальные значения для даты и времени бронирования, если они переданы.
        """
        initial = super().get_initial()

        if self.selected_date:
            try:
                initial["date"] = datetime.strptime(self.selected_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                initial["date"] = timezone.localdate()
        else:
            initial["date"] = timezone.localdate()

        if self.selected_time:
            try:
                initial["time"] = datetime.strptime(self.selected_time, "%H:%M:%S").time()
            except (ValueError, TypeError):
                pass

        return initial

    def form_valid(self, form):
        """
        При успешной валидации формы сохраняет бронирование и отправляет подтверждение.
        """
        form.instance.user = self.request.user
        form.instance.table = self.table

        response = super().form_valid(form)

        send_booking_confirmation.delay(self.object.pk)

        messages.success(self.request, "Бронирование успешно создано!")
        return response

    def _generate_time_slots(self, date_obj):
        """
        Генерирует доступные временные слоты для выбранной даты.
        Учитывает часы работы ресторана и занятость столика.
        """
        day_of_week = date_obj.weekday()
        opening_hour = 10 if day_of_week >= 5 else 11
        closing_hour = 23

        slots = []
        for hour in range(opening_hour, closing_hour + 1):
            time_obj = time(hour, 0)
            slot_end = datetime.combine(date_obj, time_obj) + timedelta(hours=1)

            conflicting_bookings = Booking.objects.filter(table=self.table, date=date_obj, status="ACTIVE")

            is_available = True
            for booking in conflicting_bookings:
                booking_start = datetime.combine(booking.date, booking.time)
                booking_end = booking_start + timedelta(hours=booking.duration)

                if datetime.combine(date_obj, time_obj) < booking_end and slot_end > booking_start:
                    is_available = False
                    break

            slots.append(
                {"time": time_obj, "is_available": is_available, "status": "free" if is_available else "booked"}
            )

        return slots

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст данные для отображения формы создания бронирования,
        включая доступные временные слоты.
        """
        context = super().get_context_data(**kwargs)

        try:
            selected_date_obj = datetime.strptime(
                self.selected_date or timezone.localdate().strftime("%Y-%m-%d"), "%Y-%m-%d"
            ).date()
        except ValueError:
            selected_date_obj = timezone.localdate()

        context.update(
            {
                "table": self.table,
                "selected_date": selected_date_obj,
                "selected_time": self.selected_time,
                "slots": self._generate_time_slots(selected_date_obj),
                "today": timezone.localdate(),
                "max_date": timezone.localdate() + timedelta(days=30),
                "default_duration": 1,
                "is_update": hasattr(self, "object"),
                "current_booking_time": getattr(self.object, "time", None),
            }
        )
        return context

    def get_success_url(self):
        return reverse_lazy("users:profile") + "?tab=active_bookings"


class BookingUpdateView(BookingBaseView, UpdateView):
    """
    Представление для редактирования существующего бронирования.
    Проверяет права пользователя, обновляет данные и отправляет уведомления об изменениях.
    """

    permission_required = "booking.can_change_reservation"
    form_class = BookingForm
    template_name = "booking/booking_form.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Инициализирует объект бронирования и проверяет права доступа.
        """
        self.object = self.get_object()
        if not request.user.has_perm("booking.can_change_reservation") and self.object.user != request.user:
            raise PermissionDenied

        self.table = self.object.table
        self.selected_date = request.GET.get("date", self.object.date.strftime("%Y-%m-%d"))
        self.selected_time = request.GET.get("time", self.object.time.strftime("%H:%M:%S"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Передаёт объект столика в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["table"] = self.table
        return kwargs

    def get_success_url(self):
        """URL для перенаправления после успешного обновления."""
        return reverse_lazy("booking:booking_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        """
        Обрабатывает успешное обновление бронирования с использованием транзакции.
        Отправляет уведомление, если изменились дата или время.
        """
        old_date = self.object.date
        old_time = self.object.time

        try:
            with transaction.atomic():
                response = super().form_valid(form)

                if (form.instance.date != old_date) or (form.instance.time != old_time):
                    send_booking_update.delay(self.object.pk, old_date, old_time)

                messages.success(self.request, "Бронирование успешно обновлено!")
                return response

        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def _generate_time_slots(self, date_obj):
        """
        Генерирует доступные временные слоты для выбранной даты.
        Учитывает часы работы ресторана и занятость столика с учетом длительности брони.
        """
        day_of_week = date_obj.weekday()
        opening_hour = 10 if day_of_week >= 5 else 11
        closing_hour = 23

        slots = []
        for hour in range(opening_hour, closing_hour + 1):
            time_obj = time(hour, 0)
            slot_start = datetime.combine(date_obj, time_obj)
            slot_end = slot_start + timedelta(hours=1)

            conflicting_bookings = Booking.objects.filter(table=self.table, date=date_obj, status="ACTIVE").exclude(
                pk=self.object.pk
            )

            is_available = True
            end_time = None

            for booking in conflicting_bookings:
                booking_start = datetime.combine(booking.date, booking.time)
                booking_end = booking_start + timedelta(hours=booking.duration)

                if slot_start < booking_end and slot_end > booking_start:
                    is_available = False
                    end_time = booking_end.time()
                    break

            slots.append(
                {
                    "time": time_obj,
                    "is_available": is_available,
                    "status": "free" if is_available else "booked",
                    "end_time": end_time,
                }
            )

        return slots

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст данные для отображения формы редактирования,
        включая доступные временные слоты с учётом текущего бронирования.
        """
        context = super().get_context_data(**kwargs)

        try:
            selected_date_obj = datetime.strptime(
                self.selected_date or timezone.localdate().strftime("%Y-%m-%d"), "%Y-%m-%d"
            ).date()
        except ValueError:
            selected_date_obj = timezone.localdate()

        context.update(
            {
                "table": self.table,
                "selected_date": selected_date_obj,
                "selected_time": self.selected_time,
                "slots": self._generate_time_slots(selected_date_obj),
                "today": timezone.localdate(),
                "max_date": timezone.localdate() + timedelta(days=30),
                "default_duration": 1,
                "is_update": hasattr(self, "object"),
                "current_booking_time": getattr(self.object, "time", None),
            }
        )
        return context


class BookingDetailView(BookingBaseView, DetailView):
    template_name = "booking/booking_detail.html"


class BookingDeleteView(BookingBaseView, DeleteView):
    """
    Представление для удаления бронирования.
    Проверяет права пользователя на удаление.
    """

    success_url = reverse_lazy("users:profile")

    def delete(self, request, *args, **kwargs):
        """
        Обрабатывает удаление бронирования с проверкой прав.
        Если нет прав, выбрасывает PermissionDenied.
        """
        try:
            self.object = self.get_object()
            if not request.user.has_perm("booking.can_delete_any_booking") and self.object.user != request.user:
                raise PermissionDenied

            return super().delete(request, *args, **kwargs)
        except Http404:
            raise PermissionDenied("Нет прав на удаление этой брони")


class BookingCancelView(BookingBaseView, UserPassesTestMixin, View):
    """
    Представление для отмены бронирования.
    Проверяет права пользователя и меняет статус бронирования на 'отменено'.
    Автоматически освобождает временной слот для новых бронирований.
    """

    permission_required = "booking.can_cancel_booking"

    def test_func(self):
        """Проверяет, имеет ли пользователь право отменять бронирования."""
        return self.request.user.has_perm(self.permission_required)

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if not request.user.has_perm("booking.can_cancel_booking") and booking.user != request.user:
            raise PermissionDenied

        if booking.status == "ACTIVE":

            table_name = booking.table.name
            date_str = booking.date.strftime("%d.%m.%Y")
            time_str = booking.time.strftime("%H:%M")

            booking.status = "CANCELLED"
            booking.save(update_fields=["status"])
            send_booking_cancellation.delay(booking.pk)

            messages.success(
                request,
                f"Бронирование столика {table_name} на {date_str} в {time_str} отменено. "
                f"Временной слот теперь доступен для бронирования.",
            )

        else:
            messages.info(request, "Бронирование уже отменено.")

        return redirect(f"{reverse('users:profile')}?tab=booking_history")
