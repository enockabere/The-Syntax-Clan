from django.urls import path
from . import views

urlpatterns = [
    path("", views.Login.as_view(), name="Login"),
    path("Admin/Registration/", views.AdminRegistrationView.as_view(), name="AdminRegistrationView"),
    path("User/Registration/", views.UserRegistrationView.as_view(), name="UserRegistrationView"),
    path('activate/<str:verification_link>/', views.ActivateAccountView.as_view(), name='activate_account'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('request-password-reset/', views.RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('password-reset-verification/<str:token>/', views.PasswordResetVerificationView.as_view(), name='password_reset_verification'),
    path('set-new-password/<str:token>/', views.SetNewPasswordView.as_view(), name='set_new_password'),
]
