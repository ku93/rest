from django.core.cache import cache

from attendance.models import Attendance


def get_cache_attendance():
    attendances = cache.get("attendance")

    if attendances:
        return attendances
    else:
        qeryset = Attendance.objects.filter(is_active=True)
        cache.set("attendance", qeryset, 180)
        return qeryset
