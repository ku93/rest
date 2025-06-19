from django.core.cache import cache

from persons.models import Employee


def get_cache_persons():
    persons = cache.get("persons")

    if persons:
        return persons
    else:
        qeryset = Employee.objects.filter(is_active=True)
        cache.set("persons", qeryset, 180)
        return qeryset
