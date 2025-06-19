from django import forms
from django.core.exceptions import ValidationError

from booking.models import Booking


class BookingForm(forms.ModelForm):
    """
    Форма для создания и редактирования бронирования столика.

    Основные функции:
    - Валидация данных бронирования
    - Проверка доступности столика на выбранное время
    - Обработка привязки к конкретному столику

    Атрибуты:
        table (Table, optional): Связанный объект столика. Если передан,
                                поле 'table' удаляется из формы.
    """

    def __init__(self, *args, table=None, **kwargs):
        """
        Инициализация формы бронирования.

        Параметры:
            table (Table, optional): Объект столика для бронирования.
                                    Если указан:
                                    - Устанавливается в экземпляр модели
                                    - Удаляется из полей формы
            *args, **kwargs: Стандартные аргументы ModelForm
        """
        super().__init__(*args, **kwargs)
        self.table = table
        if table:
            self.instance.table = table
            self.fields.pop("table", None)

    def clean(self):
        """
        Основная валидация данных формы бронирования.

        Проверяет:
        1. Что столик доступен на выбранные дату и время
        2. Что нет пересечений с другими активными бронированиями

        Исключения:
            ValidationError: Если выбранное время уже занято

        Возвращает:
            dict: Валидированные данные формы
        """
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")

        if date and time:
            existing = Booking.objects.filter(table=self.table, date=date, time=time, status="ACTIVE")

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("На выбранное время столик уже забронирован")

        return cleaned_data

    class Meta:
        """
        Метаданные формы бронирования.

        Определяет:
        - Используемую модель (Booking)
        - Отображаемые поля формы
        - Виджеты для полей ввода
        - Исключенные поля
        """

        model = Booking
        fields = ["date", "time", "duration", "person_count"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "time": forms.TimeInput(attrs={"type": "time", "step": 3600, "class": "form-control"}),
        }
        exclude = ("table",)
