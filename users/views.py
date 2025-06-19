import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (PasswordResetConfirmView,
                                       PasswordResetView)
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView

from booking.models import Booking
from config.settings import EMAIL_HOST_USER
from users.forms import LoginForm, UserRegisterForm, UserUpdateForm
from users.models import User


def login_view(request):
    """
    Представление для входа пользователя.

    Обрабатывает POST-запросы с формой входа, аутентифицирует пользователя
    по имени пользователя, email или телефону и паролю.
    При успешной аутентификации выполняет вход и перенаправляет на главную страницу.
    При ошибке отображает форму с сообщением об ошибке.
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username_or_email_or_phone"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("{% url 'attendance:index' %}")
            else:
                form.add_error(None, "Неверные данные для входа")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


class UserCreatorView(CreateView):
    """
    Представление для регистрации нового пользователя.

    Использует форму UserRegisterForm.
    При успешной регистрации создаёт пользователя неактивным,
    генерирует токен подтверждения и отправляет письмо с ссылкой для подтверждения email.
    """

    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        """
        При валидной форме создаёт пользователя с is_active=False,
        генерирует токен, сохраняет пользователя,
        отправляет письмо с подтверждением email.
        """
        user = form.save(commit=False)
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}/"
        try:
            send_mail(
                subject="Подтверждение почты",
                message=f"Привет! Перейди по ссылке для подтверждения регистрации: {url}",
                from_email=EMAIL_HOST_USER,
                recipient_list=[user.email],
            )
        except Exception:
            pass
        return super().form_valid(form)


def email_verification(request, token):
    """
    Представление для подтверждения email пользователя.

    По токену из URL находит пользователя,
    активирует его и очищает токен,
    затем перенаправляет на страницу входа.
    """
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.token = ""
    user.save()
    return redirect(reverse("users:login"))


class CustomPasswordResetView(PasswordResetView):
    """
    Кастомное представление для сброса пароля.

    Использует собственные шаблоны форм и писем.
    Проверяет, существует ли активный пользователь с указанным email,
    и отправляет письмо сброса пароля.
    """

    form_class = PasswordResetForm
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset_complete")
    subject_template_name = "users/password_reset_subject.txt"  # Добавьте этот файл

    def form_valid(self, form):
        """
        При валидной форме проверяет наличие активных пользователей с email,
        отправляет письмо сброса пароля с использованием настроек.
        Обрабатывает исключения и выводит ошибку, если письмо не удалось отправить.
        """
        email = form.cleaned_data["email"]
        active_users = User.objects.filter(email__iexact=email, is_active=True)

        if not active_users.exists():
            return super().form_valid(form)

        try:
            opts = {
                "use_https": self.request.is_secure(),
                "token_generator": default_token_generator,
                "from_email": settings.EMAIL_HOST_USER,
                "email_template_name": self.email_template_name,
                "subject_template_name": self.subject_template_name,
                "request": self.request,
                "html_email_template_name": None,
                "extra_email_context": None,
            }
            form.save(**opts)
            return super().form_valid(form)

        except Exception as e:
            print(f"Ошибка при отправке письма: {str(e)}")
            form.add_error(None, "Произошла ошибка при отправке письма. Попробуйте позже.")
            return self.form_invalid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Кастомное представление для подтверждения сброса пароля.

    Использует собственный шаблон и перенаправляет на страницу завершения сброса.
    """

    success_url = reverse_lazy("users:password_reset_complete")
    template_name = "users/password_reset_confirm.html"


class ProfileView(LoginRequiredMixin, View):
    """
    Представление профиля пользователя.

    Поддерживает отображение и редактирование данных пользователя,
    смену пароля, а также просмотр бронирований:
    - активных,
    - истории бронирований,
    - всех бронирований (для менеджеров с соответствующими правами).
    """

    def get(self, request):
        """
        Обрабатывает GET-запрос.

        Отображает профиль с выбранной вкладкой:
        'profile' (редактирование данных),
        'active_booking' (активные бронирования),
        'booking_history' (история бронирований),
        'all_bookings' (все бронирования для менеджеров).
        """
        user = request.user
        tab = request.GET.get("tab", "profile")  # Получаем активную вкладку, по умолчанию 'profile'
        editable = request.GET.get("edit") == "1"

        form = UserUpdateForm(instance=user)
        password_form = PasswordChangeForm(user)

        can_view_all_bookings = user.has_perm("booking.view_booking") and user.groups.filter(name="Менеджер").exists()

        context = {
            "tab": tab,
            "editable": editable,
            "form": form,
            "password_form": password_form,
            "user": user,
            "can_view_all_bookings": can_view_all_bookings,
        }

        if tab == "active_booking":
            active_bookings = Booking.objects.filter(user=user, status="ACTIVE").order_by("date", "time")
            context["active_bookings"] = active_bookings

        elif tab == "booking_history":
            booking_history = Booking.objects.filter(user=user, status__in=["CANCELLED", "COMPLETED"]).order_by(
                "-date", "-time"
            )
            context["booking_history"] = booking_history

        elif tab == "all_bookings" and can_view_all_bookings:
            all_bookings = Booking.objects.all().order_by("-date", "-time")
            context["all_bookings"] = all_bookings

        return render(request, "users/profile.html", context)

    def post(self, request):
        """
        Обрабатывает POST-запрос.

        Позволяет обновить данные пользователя и пароль,
        проверяет валидность форм, сохраняет изменения,
        обновляет сессию и отображает сообщения об успехе или ошибках.
        Также загружает соответствующие данные бронирований для выбранной вкладки.
        """
        user = request.user
        tab = request.GET.get("tab", "profile")
        editable = request.GET.get("edit") == "1"

        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        password_form = PasswordChangeForm(user, request.POST)

        can_view_all_bookings = user.has_perm("booking.view_booking") and user.groups.filter(name="Менеджер").exists()

        context = {
            "tab": tab,
            "editable": editable,
            "form": form,
            "password_form": password_form,
            "user": user,
            "can_view_all_bookings": can_view_all_bookings,
        }

        if form.is_valid() and password_form.is_valid():
            form.save()
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            messages.success(request, "Профиль и пароль успешно обновлены.")
            return redirect("users:profile")

        messages.error(request, "Пожалуйста, исправьте ошибки в форме.")

        if tab == "active_booking":
            active_bookings = Booking.objects.filter(user=user, status="ACTIVE").order_by("date", "time")
            context["active_bookings"] = active_bookings

        elif tab == "booking_history":
            booking_history = Booking.objects.filter(user=user, status__in=["CANCELLED", "COMPLETED"]).order_by(
                "-date", "-time"
            )
            context["booking_history"] = booking_history

        elif tab == "all_bookings" and can_view_all_bookings:
            all_bookings = Booking.objects.all().order_by("-date", "-time")
            context["all_bookings"] = all_bookings

        return render(request, "users/profile.html", context)


def logout_view(request):
    django_logout(request)
    cache.clear()
    return redirect("users:login")
