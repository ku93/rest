from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from attendance.forms import AttendanceForm, ContactForm
from attendance.models import Attendance
from attendance.tasks import send_auto_reply, send_feedback_confirmation_email
from attendance.utils import get_cache_attendance


def index(request):
    """
    Главная страница сайта с перечнем активных услуг и формой обратной связи.

    Если запрос POST и форма валидна, отправляет электронные письма:
    - подтверждение обратной связи пользователю
    - автоответ администратору

    Передает в шаблон список услуг, форму и флаг успешной отправки.
    """
    services = get_cache_attendance()
    success = False

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            subject = f"Новое сообщение от {cd['name']}"
            message = f"От: {cd['name']} <{cd['email']}>\n\n{cd['message']}"

            send_feedback_confirmation_email.delay(subject, message, cd["email"])
            send_auto_reply.delay(cd["email"], message)

            success = True
            form = ContactForm()
    else:
        form = ContactForm()

    context = {
        "services": services,
        "form": form,
        "success": success,
    }
    return render(request, "attendance/index.html", context)


class AttendanceDetailView(DetailView):
    """
    Отображение детальной информации об одной услуге.

    Кэширует страницу на 15 минут.
    """

    model = Attendance


class AttendanceCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    """
    Представление для создания новой услуги.

    Требует авторизации и права 'attendance.can_add_attendance'.

    При успешной валидации формы устанавливает текущего пользователя как владельца услуги.
    """

    model = Attendance
    form_class = AttendanceForm
    success_url = reverse_lazy("attendance:index")
    permission_required = "attendance.can_add_attendance"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Возвращает контекст для шаблона.
        """
        contex = super().get_context_data(**kwargs)
        return contex


class AttendanceUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """
    Представление для обновления существующей услуги.

    Требует авторизации и права 'attendance.can_change_attendance'.
    """

    model = Attendance
    form_class = AttendanceForm
    success_url = reverse_lazy("attendance:index")
    permission_required = "attendance.can_change_attendance"


class AttendanceDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    """
    Представление для удаления услуги.

    Требует авторизации и права 'attendance.can_delete_attendance'.
    """

    model = Attendance
    success_url = reverse_lazy("attendance:index")
    permission_required = "attendance.can_delete_attendance"
