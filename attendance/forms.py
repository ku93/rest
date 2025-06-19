from django import forms
from django.forms import BooleanField, ModelForm

from attendance.models import Attendance


class StyledFormMixin:
    """
    Миксин для добавления CSS-классов к виджетам полей формы.

    - Для полей типа BooleanField добавляет класс "form-check-input".
    - Для остальных полей добавляет класс "form-control".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class AttendanceForm(StyledFormMixin, ModelForm):
    """
    Форма для создания и редактирования модели Attendance (услуги ресторана).

    Исключает из формы поля:
    - created_at (дата создания записи)
    - updated_at (дата обновления записи)
    - owner (владелец записи)
    """

    class Meta:
        model = Attendance
        exclude = (
            "created_at",
            "updated_at",
            "owner",
        )


class ContactForm(forms.Form):
    """
    Форма обратной связи для сбора имени, email и сообщения от пользователя.

    Поля:
    - name: имя пользователя (обязательное, максимум 100 символов)
    - email: email пользователя (обязательное)
    - message: текст сообщения (обязательное, многострочное поле)

    Все поля имеют CSS-класс 'form-control' и дополнительные атрибуты для удобства отображения.
    """

    name = forms.CharField(
        label="Ваше имя",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "name",
                "required": True,
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "id": "email",
                "required": True,
            }
        ),
    )
    message = forms.CharField(
        label="Сообщение",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "id": "message",
                "rows": 4,
                "required": True,
            }
        ),
    )
