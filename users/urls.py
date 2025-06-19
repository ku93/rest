from django.contrib.auth.views import (LoginView, PasswordResetCompleteView,
                                       PasswordResetDoneView)
from django.urls import path

from users.apps import UsersConfig
from users.views import (CustomPasswordResetConfirmView,
                         CustomPasswordResetView, ProfileView, UserCreatorView,
                         email_verification, logout_view)

app_name = UsersConfig.name

urlpatterns = [
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", UserCreatorView.as_view(), name="register"),
    path("email-confirm/<str:token>/", email_verification, name="email-confirm"),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("profile/", ProfileView.as_view(), name="profile"),
]
