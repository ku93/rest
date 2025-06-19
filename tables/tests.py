from datetime import date, time

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import resolve, reverse

from tables.forms import TableForm
from tables.models import Table
from tables.views import (TableBookingSlotsView, TablesCreateView,
                          TablesDeleteView, TablesDetailView, TablesListView,
                          TablesUpdateView, generate_time_slots)
from users.models import User


class TableModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.table = Table.objects.create(
            name="VIP Booth",
            description="Уединенный столик",
            numbers=5,
            number_of_seats=4,
            location="У окна",
            is_active=True,
        )

    def test_table_creation(self):
        self.assertEqual(self.table.name, "VIP Booth")
        self.assertEqual(self.table.numbers, 5)
        self.assertTrue(self.table.is_active)

    def test_table_str_method(self):
        self.assertEqual(str(self.table), "VIP Booth")

    def test_table_ordering(self):
        Table.objects.create(name="Table 1", numbers=1, number_of_seats=2, location="Зал", is_active=True)
        tables = Table.objects.all()
        self.assertEqual(tables[0].numbers, 1)
        self.assertEqual(tables[1].numbers, 5)


class TableViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="testpass")
        cls.admin = User.objects.create_user(username="testadmin", email="admin@example.com", password="adminpass")

        # Даем права администратору
        permission_add = Permission.objects.get(codename="add_table")
        permission_change = Permission.objects.get(codename="change_table")
        permission_delete = Permission.objects.get(codename="delete_table")
        cls.admin.user_permissions.add(permission_add, permission_change, permission_delete)

        cls.table = Table.objects.create(
            name="Test Table", numbers=1, number_of_seats=4, location="Test Location", is_active=True
        )

    def setUp(self):
        self.client.login(username="testuser", password="testpass")

    def test_tables_detail_view(self):
        response = self.client.get(reverse("tables:tables_detail", kwargs={"pk": self.table.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tables/tables_detail.html")
        self.assertEqual(response.context["object"], self.table)

    def test_tables_create_view_permissions(self):

        response = self.client.get(reverse("tables:tables_create"))
        self.assertEqual(response.status_code, 403)

        self.client.login(username="testadmin", password="adminpass")
        response = self.client.get(reverse("tables:tables_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tables/tables_form.html")

    def test_tables_update_view_permissions(self):
        response = self.client.get(reverse("tables:tables_update", kwargs={"pk": self.table.pk}))
        self.assertEqual(response.status_code, 403)

        self.client.login(username="testadmin", password="adminpass")
        response = self.client.get(reverse("tables:tables_update", kwargs={"pk": self.table.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tables/tables_form.html")

    def test_tables_delete_view_permissions(self):
        response = self.client.get(reverse("tables:tables_delete", kwargs={"pk": self.table.pk}))
        self.assertEqual(response.status_code, 403)

        self.client.login(username="testadmin", password="adminpass")
        response = self.client.get(reverse("tables:tables_delete", kwargs={"pk": self.table.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tables/tables_delete.html")

    def test_generate_time_slots_weekday(self):
        test_date = date(2023, 1, 2)
        slots = generate_time_slots(test_date)
        self.assertEqual(len(slots), 23)
        self.assertEqual(slots[0], time(11, 0))
        self.assertEqual(slots[-1], time(22, 0))

    def test_generate_time_slots_weekend(self):
        test_date = date(2023, 1, 7)
        slots = generate_time_slots(test_date)
        self.assertEqual(len(slots), 25)
        self.assertEqual(slots[0], time(10, 0))
        self.assertEqual(slots[-1], time(22, 0))


class TableFormsTest(TestCase):
    def test_table_form_valid(self):
        form_data = {"name": "Test Table", "numbers": 1, "number_of_seats": 4, "location": "Test", "is_active": True}
        form = TableForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_table_form_invalid(self):
        form_data = {"name": "", "numbers": -1, "number_of_seats": 0, "location": "", "is_active": False}
        form = TableForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 5)


class TableUrlsTest(TestCase):
    def test_tables_list_url(self):
        url = reverse("tables:tables")
        self.assertEqual(resolve(url).func.view_class, TablesListView)

    def test_tables_detail_url(self):
        url = reverse("tables:tables_detail", kwargs={"pk": 1})
        self.assertEqual(resolve(url).func.view_class, TablesDetailView)

    def test_tables_create_url(self):
        url = reverse("tables:tables_create")
        self.assertEqual(resolve(url).func.view_class, TablesCreateView)

    def test_tables_update_url(self):
        url = reverse("tables:tables_update", kwargs={"pk": 1})
        self.assertEqual(resolve(url).func.view_class, TablesUpdateView)

    def test_tables_delete_url(self):
        url = reverse("tables:tables_delete", kwargs={"pk": 1})
        self.assertEqual(resolve(url).func.view_class, TablesDeleteView)

    def test_table_booking_slots_url(self):
        url = reverse("tables:table_booking_slots", kwargs={"table_number": 1, "date_str": "25.12.2023"})
        self.assertEqual(resolve(url).func.view_class, TableBookingSlotsView)
