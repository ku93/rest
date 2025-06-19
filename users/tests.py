from django.test import TestCase

from users.forms import LoginForm, UserRegisterForm, UserUpdateForm
from users.models import User


class UserModelTest(TestCase):
    """
    Тесты для модели User.
    """

    def setUp(self):
        """
        Создаёт тестового пользователя для использования в тестах.
        """
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="strongpassword123",
            phone_number="+71234567890",
            address="Test address",
        )

    def test_str_method_returns_username(self):
        """
        Проверяет, что метод __str__ возвращает имя пользователя.
        """
        self.assertEqual(str(self.user), "testuser")

    def test_email_unique_constraint(self):
        """
        Проверяет уникальность email на уровне модели при попытке создать пользователя с уже существующим email.
        Ожидает ошибку.
        """
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="anotheruser",
                email="test@example.com",
                password="anotherpassword123",
            )


class LoginFormTest(TestCase):
    """
    Тесты для формы LoginForm.
    """

    def test_valid_data(self):
        """
        Проверяет корректную валидацию формы при заполнении валидных данных.
        """
        form = LoginForm(
            data={
                "username_or_email_or_phone": "testuser",
                "password": "password123",
            }
        )
        self.assertTrue(form.is_valid())

    def test_missing_password(self):
        """
        Проверяет, что форма невалидна при отсутствии пароля и возвращает ошибку для поля password.
        """
        form = LoginForm(
            data={
                "username_or_email_or_phone": "testuser",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class UserRegisterFormTest(TestCase):
    """
    Тесты для формы регистрации UserRegisterForm.
    """

    def test_valid_form(self):
        """
        Проверяет, что форма валидна при корректных данных.
        """
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "phone_number": "+79998887766",
            "address": "New address",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_email_uniqueness_validation(self):
        """
        Проверяет, что форма невалидна при попытке зарегистрировать пользователя с уже существующим email,
        и что возвращается соответствующая ошибка в поле email.
        """
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="password123",
        )
        form_data = {
            "username": "anotheruser",
            "email": "existing@example.com",
            "phone_number": "+79998887766",
            "address": "Address",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"][0], "Пользователь с таким email уже существует.")

    def test_password_mismatch(self):
        """
        Проверяет, что форма невалидна при несовпадении паролей и возвращает ошибку в поле password2.
        """
        form_data = {
            "username": "user",
            "email": "user@example.com",
            "phone_number": "+79998887766",
            "address": "Address",
            "password1": "ComplexPass123!",
            "password2": "WrongPass123!",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class UserUpdateFormTests(TestCase):
    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="OldFirst",
            last_name="OldLast",
        )

    def test_address_widget_rows(self):
        """
        Проверяет, что виджет поля address имеет атрибут rows равный 3.
        """
        form = UserUpdateForm(instance=self.user)
        self.assertIn("address", form.fields)
        widget = form.fields["address"].widget
        self.assertEqual(widget.attrs.get("rows"), 3)
