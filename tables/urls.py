from django.urls import path

from tables.apps import TablesConfig
from tables.views import (TableBookingSlotsView, TablesCreateView,
                          TablesDeleteView, TablesDetailView, TablesListView,
                          TablesUpdateView)

app_name = TablesConfig.name

urlpatterns = [
    path("tables/", TablesListView.as_view(), name="tables"),
    path("tables/<int:pk>/", TablesDetailView.as_view(), name="tables_detail"),
    path("tables/<int:pk>/update/", TablesUpdateView.as_view(), name="tables_update"),
    path("tables/<int:pk>/delete/", TablesDeleteView.as_view(), name="tables_delete"),
    path("tables/create/", TablesCreateView.as_view(), name="tables_create"),
    path(
        "table/<int:table_number>/<str:date_str>/slots/",
        TableBookingSlotsView.as_view(),
        name="table_booking_slots",
    ),
]
