from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from tables.forms import TableForm
from tables.models import Table
from tables.utils import get_cache_tables


def generate_time_slots(date, step_minutes=30, slot_duration=timedelta(hours=1)):
    """
    Генерирует список времен начала слотов для заданной даты с шагом step_minutes,
    учитывая рабочие часы ресторана (будни и выходные).
    Учитывает длительность слота, чтобы последний слот не выходил за рабочее время.
    :param date: datetime.date
    :param step_minutes: int — шаг между слотами в минутах
    :param slot_duration: timedelta — длительность одного слота
    :return: list[datetime.time] — список времен начала слотов
    """
    weekday = date.weekday()
    if weekday < 5:  # Пн-Пт
        open_time = time(11, 0)
        close_time = time(23, 0)
    else:  # Сб-Вс
        open_time = time(10, 0)
        close_time = time(23, 0)

    slots = []
    current_dt = datetime.combine(date, open_time)
    close_dt = datetime.combine(date, close_time)

    while current_dt + slot_duration <= close_dt:
        slots.append(current_dt.time())
        current_dt += timedelta(minutes=step_minutes)

    return slots


class TablesListView(ListView):
    """
    Представление списка активных столиков.
    Доступно всем пользователям (без ограничений).
    Отображает только столики с is_active=True.
    В контекст добавляет актуальное состояние доступности столиков,
    обновляя их методом get_availability_statuses с текущей датой и временем.
    """

    model = Table
    template_name = "tables/tables_list.html"
    context_object_name = "tables"

    def get_queryset(self):
        return get_cache_tables()


class TablesDetailView(DetailView):
    """
    Представление детальной информации о столике.
    Доступно всем пользователям.
    Кэширует страницу на 15 минут для повышения производительности.
    """

    model = Table
    template_name = "tables/tables_detail.html"

    SLOT_DURATION = timedelta(hours=1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()
        date_str_get = self.request.GET.get("date", today.strftime("%Y-%m-%d"))

        try:
            date_obj = datetime.strptime(date_str_get, "%Y-%m-%d").date()
        except ValueError:
            date_obj = today

        max_date = today + timedelta(days=30)

        slots = self.get_slots_for_date(date_obj)

        date_str_for_url = date_obj.strftime("%d.%m.%Y")

        context.update(
            {
                "today": today,
                "date": date_obj,
                "date_str": date_str_for_url,
                "max_date": max_date.strftime("%Y-%m-%d"),
                "slots": slots,
            }
        )
        return context

    def get_slots_for_date(self, date_obj):
        slots = generate_time_slots(date_obj, step_minutes=60, slot_duration=self.SLOT_DURATION)
        statuses = self.object.get_availability_statuses(date_obj, slots, slot_duration=self.SLOT_DURATION)
        slots_list = []
        for slot_time in slots:
            slots_list.append(
                {
                    "time": slot_time.strftime("%H:%M"),
                    "status": statuses.get(slot_time, "free"),
                }
            )
        return slots_list


class TablesCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    """
    Представление для создания нового столика.
    Доступно только аутентифицированным пользователям с правом 'tables.add_table'.
    Использует форму TableForm.
    После успешного создания перенаправляет на список столиков.
    """

    model = Table
    form_class = TableForm
    template_name = "tables/tables_form.html"
    success_url = reverse_lazy("tables:tables")
    permission_required = "tables.add_table"


class TablesUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """
    Представление для обновления существующего столика.
    Доступно только аутентифицированным пользователям с правом 'tables.change_table'.
    Использует форму TableForm.
    После успешного обновления перенаправляет на список столиков.
    """

    model = Table
    form_class = TableForm
    template_name = "tables/tables_form.html"
    success_url = reverse_lazy("tables:tables")
    permission_required = "tables.change_table"


class TablesDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    """
    Представление для удаления столика.
    Доступно только аутентифицированным пользователям с правом 'tables.delete_table'.
    После успешного удаления перенаправляет на список столиков.
    """

    model = Table
    template_name = "tables/tables_delete.html"
    success_url = reverse_lazy("tables:tables")
    permission_required = "tables.delete_table"


class TableBookingSlotsView(LoginRequiredMixin, View):
    """
    Отображает список временных слотов столика с индикацией статусов занятости,
    используя метод модели Table.get_availability_statuses.
    Учитывает длительность бронирований (slot_duration) и закрывает все слоты,
    которые перекрываются с интервалом бронирования.
    URL: /booking/table/<table_number>/<date_str>/slots/
    """

    SLOT_DURATION = timedelta(hours=1)

    def get(self, request, table_number, date_str):
        table = get_object_or_404(Table, numbers=table_number)
        try:
            date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            messages.error(request, "Ошибка: введённая дата некорректна!")
            return redirect("tables:tables")

        slots = generate_time_slots(date, step_minutes=60, slot_duration=self.SLOT_DURATION)

        statuses = table.get_availability_statuses(date, slots, slot_duration=self.SLOT_DURATION)

        slot_status_list = [
            {
                "time": slot_time.strftime("%H:%M"),
                "status": statuses.get(slot_time, "free"),
            }
            for slot_time in slots
        ]

        context = {
            "table": table,
            "date": date,
            "slots": slot_status_list,
        }
        return render(request, "booking/table_booking_slots.html", context)
