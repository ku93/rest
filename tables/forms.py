from django.forms import ModelForm

from tables.models import Table


class TableForm(ModelForm):
    """
    Форма для создания и редактирования столиков ресторана.

    Наследуется от ModelForm, предоставляя стандартную функциональность
    Django для работы с моделями через формы. Автоматически генерирует
    поля формы на основе модели Table.

    Особенности:
    - Включает все поля модели Table
    - Автоматическая валидация данных на основе модели
    - Поддержка виджетов по умолчанию для каждого типа поля

    Пример использования:
    >>> form = TableForm(data={
    ...     'numbers': 5,
    ...     'name': 'VIP Booth',
    ...     'number_of_seats': 6,
    ...     'description': 'Уединенный VIP-столик'
    ... })
    >>> if form.is_valid():
    ...     table = form.save()
    """

    class Meta:
        """
        Внутренний класс для конфигурации формы.

        Атрибуты:
            model (Table): Связывает форму с моделью Table. Определяет,
                          структуру и поведение формы на основе модели.

            fields (str): Указывает, какие поля модели должны быть включены
                         в форму. Значение "__all__" включает все поля модели.

        Включаемые поля модели Table:
        - numbers: Номер столика (IntegerField)
        - name: Название столика (CharField)
        - number_of_seats: Количество мест (PositiveIntegerField)
        - description: Описание столика (TextField)

        """

        model = Table
        fields = "__all__"
