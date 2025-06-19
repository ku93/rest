from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """
    Кастомная модель пользователя, расширяющая стандартную AbstractUser.

    Атрибуты:
        username (CharField): Уникальное имя пользователя, отображаемое в интерфейсе.
        email (EmailField): Уникальный адрес электронной почты пользователя.
        phone_number (PhoneNumberField): Номер телефона пользователя для связи (необязательное поле).
        address (TextField): Адрес пользователя.
        avatar (ImageField): Изображение аватара пользователя (необязательное поле).
        token (CharField): Токен для подтверждения email или других целей (необязательное поле).
    """

    username = models.CharField(
        unique=True,
        verbose_name="Имя пользователя",
        max_length=255,
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта пользователя",
    )
    phone_number = PhoneNumberField(
        verbose_name="Номер телефона",
        null=True,
        blank=True,
        help_text="Пожалуйста введите номер телефона для связи с вами",
    )
    address = models.TextField(verbose_name="Адрес")
    avatar = models.ImageField(verbose_name="Аватар", null=True, blank=True)
    token = models.CharField(
        max_length=100,
        verbose_name="Token",
        blank=True,
        null=True,
        help_text="Токен для подтверждения email или иных целей",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        """
        Возвращает строковое представление пользователя — его имя пользователя.
        """
        return self.username
