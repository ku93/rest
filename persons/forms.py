from django.forms import DateInput, ModelForm

from .models import Employee


class EmployeeForm(ModelForm):
    """
    Форма для создания и редактирования карточек сотрудников.

    Использует модель Employee.

    Исключает из формы поля:
        - created_at (дата создания записи)
        - updated_at (дата обновления записи)
        - owner (владелец записи)

    Виджеты:
        Для полей даты ('birth_date', 'getting_started', 'getting_started_in_restaurant')
        используется HTML5 input с типом 'date' для удобного выбора даты в браузере.
    """

    class Meta:
        model = Employee
        exclude = (
            "created_at",
            "updated_at",
            "owner",
        )
        widgets = {
            "birth_date": DateInput(attrs={"type": "date"}),
            "getting_started": DateInput(attrs={"type": "date"}),
            "getting_started_in_restaurant": DateInput(attrs={"type": "date"}),
        }
