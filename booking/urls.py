from django.urls import path

from booking.apps import BookingConfig
from booking.views import (BookingCancelView, BookingCreateView,
                           BookingDeleteView, BookingDetailView,
                           BookingListView, BookingUpdateView)

app_name = BookingConfig.name
urlpatterns = [
    path("", BookingListView.as_view(), name="booking_list"),
    path("<int:table_number>/create/", BookingCreateView.as_view(), name="booking_create"),
    path("<int:pk>/", BookingDetailView.as_view(), name="booking_detail"),
    path("<int:pk>/update/", BookingUpdateView.as_view(), name="booking_update"),
    path("<int:pk>/delete/", BookingDeleteView.as_view(), name="booking_delete"),
    path("<int:pk>/detail/", BookingDetailView.as_view(), name="booking_detail"),
    path("<int:pk>/cancel/", BookingCancelView.as_view(), name="booking_cancel"),
]
