from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from attendance.models import Attendance
from booking.models import Booking
from users.models import User


class Command(BaseCommand):
    help = "Создание групп и назначение прав"

    def handle(self, *args, **options):
        guest_group, _ = Group.objects.get_or_create(name="Гость")
        user_group, _ = Group.objects.get_or_create(name="Пользователь")
        manager_group, _ = Group.objects.get_or_create(name="Менеджер")

        booking_ct = ContentType.objects.get_for_model(Booking)
        user_ct = ContentType.objects.get_for_model(User)
        table_ct = ContentType.objects.get(app_label="tables", model="table")
        employee_ct = ContentType.objects.get(app_label="persons", model="employee")
        attendance_ct = ContentType.objects.get_for_model(Attendance)

        can_reserve = Permission.objects.get(codename="can_reserve", content_type=booking_ct)
        can_view_all_bookings = Permission.objects.get(codename="can_view_all_bookings", content_type=booking_ct)
        can_change_reservation = Permission.objects.get(codename="can_change_reservation", content_type=booking_ct)
        can_delete_any_booking = Permission.objects.get(codename="can_delete_any_booking", content_type=booking_ct)
        can_cancel_booking = Permission.objects.get(codename="can_cancel_booking", content_type=booking_ct)

        can_add_attendance = Permission.objects.get(codename="can_add_attendance", content_type=attendance_ct)
        can_change_attendance = Permission.objects.get(codename="can_change_attendance", content_type=attendance_ct)
        can_delete_attendance = Permission.objects.get(codename="can_delete_attendance", content_type=attendance_ct)

        user_permissions = [
            Permission.objects.get(codename="add_booking", content_type=booking_ct),
            Permission.objects.get(codename="view_booking", content_type=booking_ct),
            Permission.objects.get(codename="change_booking", content_type=booking_ct),
            Permission.objects.get(codename="delete_booking", content_type=booking_ct),
            can_reserve,
            can_cancel_booking,
            Permission.objects.get(codename="change_user", content_type=user_ct),
            Permission.objects.get(codename="view_user", content_type=user_ct),
        ]
        user_group.permissions.set(user_permissions)

        manager_permissions = [
            Permission.objects.get(codename="add_booking", content_type=booking_ct),
            Permission.objects.get(codename="view_booking", content_type=booking_ct),
            Permission.objects.get(codename="change_booking", content_type=booking_ct),
            Permission.objects.get(codename="delete_booking", content_type=booking_ct),
            can_reserve,
            can_view_all_bookings,
            can_change_reservation,
            can_delete_any_booking,
            can_cancel_booking,
            Permission.objects.get(codename="add_user", content_type=user_ct),
            Permission.objects.get(codename="view_user", content_type=user_ct),
            Permission.objects.get(codename="change_user", content_type=user_ct),
            Permission.objects.get(codename="delete_user", content_type=user_ct),
            Permission.objects.get(codename="add_table", content_type=table_ct),
            Permission.objects.get(codename="view_table", content_type=table_ct),
            Permission.objects.get(codename="change_table", content_type=table_ct),
            Permission.objects.get(codename="delete_table", content_type=table_ct),
            Permission.objects.get(codename="add_employee", content_type=employee_ct),
            Permission.objects.get(codename="view_employee", content_type=employee_ct),
            Permission.objects.get(codename="change_employee", content_type=employee_ct),
            Permission.objects.get(codename="delete_employee", content_type=employee_ct),
            can_add_attendance,
            can_change_attendance,
            can_delete_attendance,
        ]
        manager_group.permissions.set(manager_permissions)

        guest_group.permissions.clear()

        self.stdout.write(self.style.SUCCESS("Группы и права успешно созданы и назначены"))
