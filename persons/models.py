from datetime import date

from django.db import models

from users.models import User


class Employee(models.Model):
    """
    Модель, описывающая сотрудника ресторана.

    Атрибуты:
        photo (ImageField): Фотография сотрудника, загружается в папку 'employee/', необязательное поле.
        name (CharField): ФИО сотрудника, максимум 100 символов.
        birth_date (DateField): Дата рождения сотрудника, необязательное поле.
        post (CharField): Должность сотрудника, максимум 100 символов.
        description (TextField): Описание должностных обязанностей сотрудника.
        getting_started (DateField): Дата начала работы на текущей должности.
        getting_started_in_restaurant (DateField): Дата начала работы в ресторане.
        is_active (BooleanField): Активен ли сотрудник (по умолчанию True).
        created_at (DateTimeField): Дата и время создания записи (устанавливается автоматически).
        updated_at (DateTimeField): Дата и время последнего изменения записи (обновляется автоматически).
        owner (ForeignKey): Владелец записи (пользователь), связанный с моделью User, при удалении пользователя удаляет
        запись.

    Методы:
        full_years(): Возвращает полный возраст сотрудника в годах, вычисленный на основе birth_date.
                      Если дата рождения не указана, возвращает None.

    Метаданные:
        verbose_name: Отображаемое название модели в единственном числе — 'Сотрудник'.
        verbose_name_plural: Отображаемое название модели во множественном числе — 'Сотрудники'.

    Строковое представление:
        Возвращает имя сотрудника (name).
    """

    photo = models.ImageField(
        upload_to="employee/",
        null=True,
        blank=True,
        verbose_name="Фотография сотрудника",
    )
    name = models.CharField(max_length=100, verbose_name="ФИО сотрудника")
    birth_date = models.DateField(verbose_name="Дата рождения сотрудника", blank=True, null=True)
    post = models.CharField(max_length=100, verbose_name="Должность сотрудника")
    description = models.TextField(verbose_name="Описание должностных обязанностей сотрудника")
    getting_started = models.DateField(verbose_name="Начало работы в этой должности")
    getting_started_in_restaurant = models.DateField(verbose_name="Начало работы в ресторане")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания карточки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения карточки")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    def full_years(self):
        """
        Вычисляет полный возраст сотрудника в годах по дате рождения.

        Возвращает:
            int | None: Возраст в полных годах или None, если дата рождения не указана.
        """
        if not self.birth_date:
            return None
        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        """
        Строковое представление объекта — возвращает ФИО сотрудника.

        Returns:
            str: имя сотрудника.
        """
        return self.name
