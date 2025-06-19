from django.core.cache import cache

from tables.models import Table


def get_cache_tables():
    tables = cache.get("tables")

    if tables:
        return tables
    else:
        qeryset = Table.objects.filter(is_active=True)
        cache.set("tables", qeryset, 180)
        return qeryset
