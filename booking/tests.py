from datetime import datetime, timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from booking.forms import BookingForm
from booking.models import Booking
from booking.views import (BookingCancelView, BookingCreateView,
                           BookingDeleteView, BookingDetailView,
                           BookingUpdateView)
from tables.models import Table
from users.models import User


class BookingModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass")
        cls.table = Table.objects.create(
            name="Test Table", numbers=1, number_of_seats=4, location="Test", is_active=True
        )
        cls.booking = Booking.objects.create(
            user=cls.user,
            table=cls.table,
            date=timezone.now().date() + timedelta(days=1),
            time=datetime.strptime("12:00", "%H:%M").time(),
            duration=2,
            person_count=2,
        )

    def test_booking_creation(self):
        self.assertEqual(self.booking.status, "ACTIVE")
        self.assertEqual(self.booking.table.name, "Test Table")
        self.assertEqual(self.booking.user.username, "testuser")

    def test_booking_str_method(self):
        expected_str = f"{self.table} - {self.booking.date} {self.booking.time.strftime('%H:%M')} ({self.user})"
        self.assertEqual(str(self.booking), expected_str)

    def test_booking_status_choices(self):
        self.assertEqual(
            Booking.STATUS_CHOICES,
            [
                ("ACTIVE", "Активно"),
                ("CANCELLED", "Отменено"),
                ("COMPLETED", "Завершено"),
            ],
        )


class BookingFormsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass")
        cls.table = Table.objects.create(
            name="Test Table", numbers=1, number_of_seats=4, location="Test", is_active=True
        )

    def test_booking_form_valid(self):
        form_data = {
            "date": timezone.now().date() + timedelta(days=1),
            "time": "12:00",
            "duration": 2,
            "person_count": 2,
        }
        form = BookingForm(data=form_data, table=self.table)
        self.assertTrue(form.is_valid())

    def test_booking_form_invalid(self):
        form_data = {
            "date": timezone.now().date() - timedelta(days=1),
            "time": "12:00",
            "duration": 0,
            "person_count": 5,
        }
        form = BookingForm(data=form_data, table=self.table)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)


class BookingViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass")
        cls.admin = User.objects.create_user(username="admin", email="admin@example.com", password="adminpass")

        # Даем права администратору
        permissions = Permission.objects.filter(
            codename__in=[
                "can_view_all_bookings",
                "can_change_reservation",
                "can_delete_any_booking",
                "can_cancel_booking",
            ]
        )
        cls.admin.user_permissions.set(permissions)

        cls.table = Table.objects.create(
            name="Test Table", numbers=1, number_of_seats=4, location="Test", is_active=True
        )
        cls.booking = Booking.objects.create(
            user=cls.user,
            table=cls.table,
            date=timezone.now().date() + timedelta(days=1),
            time=datetime.strptime("12:00", "%H:%M").time(),
            duration=2,
            person_count=2,
        )

    def setUp(self):
        self.client.login(username="testuser", password="testpass")

    def test_booking_create_view(self):
        test_date = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        url = reverse("booking:booking_create", kwargs={"table_number": self.table.numbers})
        url += f"?date={test_date}&time=12:00"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "booking/booking_form.html")
        self.assertIn("form", response.context)

    def test_booking_update_view_permissions(self):
        # Обычный пользователь может редактировать свои брони
        response = self.client.get(reverse("booking:booking_update", kwargs={"pk": self.booking.pk}))
        self.assertEqual(response.status_code, 200)

        # Администратор может редактировать любые брони
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("booking:booking_update", kwargs={"pk": self.booking.pk}))
        self.assertEqual(response.status_code, 200)

    def test_booking_cancel_view(self):
        response = self.client.post(reverse("booking:booking_cancel", kwargs={"pk": self.booking.pk}))
        self.assertEqual(response.status_code, 403)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "ACTIVE")

    def test_booking_detail_view(self):
        response = self.client.get(reverse("booking:booking_detail", kwargs={"pk": self.booking.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "booking/booking_detail.html")


class BookingUrlsTest(TestCase):
    def test_booking_list_url(self):
        url = reverse("users:profile") + "?tab=active_bookings"
        self.assertEqual(url, "/users/profile/?tab=active_bookings")

    def test_booking_create_url(self):
        url = reverse("booking:booking_create", kwargs={"table_number": 1})
        self.assertEqual(resolve(url).func.view_class, BookingCreateView)

    def test_booking_update_url(self):
        url = reverse("booking:booking_update", kwargs={"pk": 1})
        self.assertEqual(resolve(url).func.view_class, BookingUpdateView)

    def test_booking_delete_url(self):
        url = reverse("booking:booking_delete", kwargs={"pk": 1})
        self.assertEqual(resolve(url).func.view_class, BookingDeleteView)

    def test_booking_detail_url(self):
        url = reverse("booking:booking_detail", kwargs={"pk": 1})
        self.assertEqual(resolve(url).func.view_class, BookingDetailView)

    def test_booking_cancel_url(self):
        url = reverse("booking:booking_cancel", kwargs={"pk": 1})
        self.assertEqual(resolve(url).func.view_class, BookingCancelView)
