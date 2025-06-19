from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from users.models import User


class LoginForm(forms.Form):
    """
    Форма для входа пользователя.

    Поля:
        username_or_email_or_phone (CharField): Имя пользователя, email или номер телефона для аутентификации.
        password (CharField): Пароль пользователя.
    """

    username_or_email_or_phone = forms.CharField(label="Имя пользователя, email или телефон")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


class UserRegisterForm(UserCreationForm):
    """
    Форма регистрации нового пользователя.

    Наследуется от UserCreationForm и расширяет поля модели User:
    username, email, phone_number, address, avatar, password1, password2.

    Валидация:
        Проверяет уникальность email.
    """

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone_number",
            "address",
            "avatar",
            "password1",
            "password2",
        )

    def clean_email(self):
        """
        Проверяет, что email уникален в базе.

        Возвращает:
            email (str): Валидный email.

        Вызывает:
            ValidationError: если email уже зарегистрирован.
        """
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email


class UserUpdateForm(forms.ModelForm):
    """
    Форма для обновления данных пользователя.

    Поля:
        username, email, first_name, last_name, phone_number, address, avatar.

    Виджеты:
        address — многострочное текстовое поле с 3 строками.
    """

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "avatar",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }
