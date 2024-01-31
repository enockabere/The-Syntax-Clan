from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class IdNumberBackend(ModelBackend):
    def authenticate(self, request, id_number=None, password=None, **kwargs):
        UserModel = get_user_model()

        try:
            user = UserModel.objects.get(id_number=id_number)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()

        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
