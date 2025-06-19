from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from persons.apps import PersonsConfig
from persons.views import (EmployeeCreateView, EmployeeDeleteView,
                           EmployeeDetailView, EmployeeListView,
                           EmployeeUpdateView, restaurants)

app_name = PersonsConfig.name

urlpatterns = [
    path("restaurant/", restaurants, name="restaurant"),
    path("employee/<int:pk>/", EmployeeDetailView.as_view(), name="employee_detail"),
    path("employee_create/", EmployeeCreateView.as_view(), name="employee_create"),
    path("employee_list/", EmployeeListView.as_view(), name="employee_list"),
    path(
        "employee/<int:pk>/update/",
        EmployeeUpdateView.as_view(),
        name="employee_update",
    ),
    path(
        "employee/<int:pk>/delete/",
        EmployeeDeleteView.as_view(),
        name="employee_delete",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
