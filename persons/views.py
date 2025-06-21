from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from persons.forms import EmployeeForm
from persons.models import Employee
from persons.utils import get_cache_persons


def restaurants(request):
    """
    Отображает страницу ресторана с активными сотрудниками.

    Контекст:
        employees (QuerySet): список активных сотрудников (is_active=True).

    Шаблон:
        persons/restaurant.html
    """
    employees = Employee.objects.filter(is_active=True)
    context = {
        "employees": employees,
    }
    return render(request, "persons/restaurant.html", context)


class EmployeeDetailView(DetailView):
    """
    Представление для детального просмотра карточки сотрудника.

    Модель:
        Employee

    Кэширование:
        Страница кэшируется на 15 минут (60 * 15 секунд).
    """

    model = Employee


class EmployeeCreateView(PermissionRequiredMixin, CreateView):
    """
    Представление для создания новой карточки сотрудника.

    Модель:
        Employee

    Форма:
        EmployeeForm

    Права доступа:
        Пользователь должен иметь соответствующие права (по умолчанию permission_required отсутствует,
        можно добавить при необходимости).

    При успешном сохранении:
        Перенаправляет на страницу ресторана ('persons:restaurant').

    Особенности:
        В методе form_valid устанавливает владельца карточки как текущего пользователя.
    """

    model = Employee
    form_class = EmployeeForm
    success_url = reverse_lazy("persons:restaurant")
    permission_required = 'employees.add_employee'

    def form_valid(self, form):
        """
        Устанавливает владельца карточки сотрудника перед сохранением формы.

        Args:
            form (EmployeeForm): форма с данными сотрудника.

        Returns:
            HttpResponseRedirect: стандартный ответ после успешного сохранения.
        """
        form.instance.owner = self.request.user
        return super().form_valid(form)


class EmployeeListView(ListView):
    """
    Представление для отображения списка активных сотрудников.

    Модель:
        Employee

    Шаблон:
        persons/employee_list.html

    Контекст:
        employees (QuerySet): активные сотрудники (is_active=True).

    Переопределённый метод:
        get_queryset() - возвращает только активных сотрудников.
    """

    model = Employee
    template_name = "persons/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        """
        Возвращает queryset активных сотрудников.

        Returns:
            QuerySet: сотрудники с is_active=True.
        """
        return get_cache_persons()


class EmployeeUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Представление для обновления информации о сотруднике.

    Модель:
        Employee

    Форма:
        EmployeeForm

    Права доступа:
        Пользователь должен иметь permission 'persons.change_employee'.

    При успешном сохранении:
        Перенаправляет на страницу ресторана ('persons:restaurant').

    Дополнительная проверка:
        Метод test_func проверяет, что текущий пользователь является владельцем карточки сотрудника.
    """

    model = Employee
    form_class = EmployeeForm
    success_url = reverse_lazy("persons:restaurant")
    permission_required = "persons.change_employee"

    def test_func(self):
        """
        Проверяет, что текущий пользователь является владельцем редактируемого сотрудника.

        Returns:
            bool: True, если пользователь — владелец, иначе False.
        """
        employee = self.get_object()
        return employee.owner == self.request.user


class EmployeeDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Представление для удаления карточки сотрудника.

    Модель:
        Employee

    Права доступа:
        Пользователь должен иметь permission 'persons.delete_employee'.

    При успешном удалении:
        Перенаправляет на страницу ресторана ('persons:restaurant').

    Дополнительная проверка:
        Метод test_func проверяет, что текущий пользователь является владельцем удаляемого сотрудника.
    """

    model = Employee
    success_url = reverse_lazy("persons:restaurant")
    permission_required = "persons.delete_employee"

    def test_func(self):
        """
        Проверяет, что текущий пользователь является владельцем удаляемого сотрудника.

        Returns:
            bool: True, если пользователь — владелец, иначе False.
        """
        employee = self.get_object()
        return employee.owner == self.request.user
