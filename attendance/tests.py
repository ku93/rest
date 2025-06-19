from django.test import RequestFactory, TestCase

from attendance.forms import ContactForm
from attendance.models import Attendance
from attendance.views import AttendanceDetailView
from users.models import User


class AttendanceModelTest(TestCase):
    """
    Unit-тесты для модели Attendance.
    Проверяется корректность строкового представления и мета-атрибутов модели.
    """

    def setUp(self):
        """
        Создание тестового пользователя и объекта Attendance,
        который будет использоваться в тестах.
        """
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.attendance = Attendance.objects.create(
            name="Test Service",
            description="Test description",
            price=100,
            owner=self.user,
        )

    def test_str_method(self):
        """
        Проверяет, что метод __str__ модели возвращает ожидаемое строковое представление.
        """
        self.assertEqual(str(self.attendance), "Test Service")

    def test_verbose_names(self):
        """
        Проверяет, что verbose_name и verbose_name_plural модели установлены правильно.
        """
        self.assertEqual(Attendance._meta.verbose_name, "Услуга")
        self.assertEqual(Attendance._meta.verbose_name_plural, "Услуги")


class ContactFormTest(TestCase):
    """
    Unit-тесты для формы ContactForm.
    Проверяется валидность формы при корректных и некорректных данных.
    """

    def test_form_valid_data(self):
        """
        Проверяет, что форма валидна при передаче корректных данных.
        """
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "message": "Hello!",
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        """
        Проверяет, что форма невалидна при передаче некорректных данных.
        """
        form_data = {
            "name": "",
            "email": "not-an-email",
            "message": "",
        }
        form = ContactForm(data=form_data)
        self.assertFalse(form.is_valid())


class AttendanceDetailViewUnitTest(TestCase):
    """
    Unit-тест для метода get_object DetailView без использования HTTP-запросов.
    Позволяет проверить, что вьюшка корректно возвращает объект модели по pk.
    """

    def setUp(self):
        """
        Создание RequestFactory для имитации запроса и тестового объекта Attendance.
        """
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.attendance = Attendance.objects.create(
            name="Detail Service",
            description="Detail description",
            price=150,
            owner=self.user,
        )

    def test_get_object(self):
        """
        Проверяет, что метод get_object возвращает правильный объект Attendance.
        """
        request = self.factory.get(f"/attendance/{self.attendance.pk}/")
        view = AttendanceDetailView()
        view.setup(request, pk=self.attendance.pk)
        obj = view.get_object()
        self.assertEqual(obj, self.attendance)
