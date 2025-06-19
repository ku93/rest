from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Employee

User = get_user_model()


class EmployeeModelTests(TestCase):
    def setUp(self):
        """
        Создает пользователя для использования в тестах модели Employee.
        """
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_employee_creation(self):
        """
        Проверяет успешное создание объекта Employee с корректными данными.
        Также проверяет, что поле photo по умолчанию пустое (отсутствует).
        """
        employee = Employee.objects.create(
            owner=self.user,
            name="Иван Иванов",
            birth_date=date(1990, 5, 20),
            post="Повар",
            description="Приготовление блюд",
            getting_started=date(2020, 1, 1),
            getting_started_in_restaurant=date(2018, 6, 15),
            is_active=True,
        )
        self.assertEqual(employee.name, "Иван Иванов")
        self.assertEqual(employee.post, "Повар")
        self.assertTrue(employee.is_active)
        self.assertEqual(employee.owner, self.user)
        self.assertFalse(employee.photo)

    def test_full_years_with_birth_date(self):
        """
        Проверяет, что метод full_years() корректно вычисляет возраст сотрудника.
        Для детерминированного результата используется мок текущей даты (fixed_today).
        Дата рождения установлена так, чтобы возраст был ровно 30 лет на fixed_today.
        """
        fixed_today = date(2024, 6, 15)
        birth_date = date(1994, 6, 15)  # ровно 30 лет на fixed_today

        with patch("persons.models.date") as mock_date:
            mock_date.today.return_value = fixed_today
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            employee = Employee.objects.create(
                owner=self.user,
                name="Мария Петрова",
                birth_date=birth_date,
                post="Официант",
                description="Обслуживание гостей",
                getting_started=date(2022, 3, 1),
                getting_started_in_restaurant=date(2021, 5, 10),
                is_active=True,
            )
            self.assertEqual(employee.full_years(), 30)

    def test_full_years_no_birth_date(self):
        """
        Проверяет, что метод full_years() возвращает None,
        если дата рождения не указана.
        """
        employee = Employee.objects.create(
            owner=self.user,
            name="Алексей Смирнов",
            birth_date=None,
            post="Бармен",
            description="Приготовление напитков",
            getting_started=date(2023, 1, 10),
            getting_started_in_restaurant=date(2020, 8, 5),
            is_active=True,
        )
        self.assertIsNone(employee.full_years())

    def test_str_method_returns_name(self):
        """
        Проверяет, что строковое представление объекта Employee
        возвращает имя сотрудника.
        """
        employee = Employee.objects.create(
            owner=self.user,
            name="Елена Кузнецова",
            birth_date=date(1985, 12, 1),
            post="Менеджер",
            description="Управление персоналом",
            getting_started=date(2019, 7, 15),
            getting_started_in_restaurant=date(2017, 4, 20),
            is_active=True,
        )
        self.assertEqual(str(employee), "Елена Кузнецова")
