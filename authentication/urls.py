from django.urls import path
from . import views

urlpatterns = [
    path("", views.Login.as_view(), name="Login"),
    path("Register/", views.Register.as_view(), name="Register"),
    path("profile", views.profile, name="profile"),
    path("verify", views.verifyRequest, name="verify"),
    path("ResendEmail/", views.ResendEmail.as_view(), name="ResendEmail"),
    path("resetPassword", views.ResetPassword.as_view(), name="resetPassword"),
    path("reset", views.reset_request.as_view(), name="reset"),
    path(
        "ResendResetToken/", views.ResendResetToken.as_view(), name="ResendResetToken"
    ),
    path("Admin/Registration/", views.AdminRegistrationView.as_view(), name="AdminRegistrationView"),
]
