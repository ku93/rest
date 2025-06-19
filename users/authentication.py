from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class UsernameEmailPhoneBackend(ModelBackend):
    """
    Позволяет аутентифицироваться по username, email или phone_number.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                try:
                    user = UserModel.objects.get(phone_number=username)
                except UserModel.DoesNotExist:
                    return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
