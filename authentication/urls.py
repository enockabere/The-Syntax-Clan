from django.urls import path
from . import views

urlpatterns = [
    path("", views.Login.as_view(), name="Login"),
    path("Admin/Registration/", views.AdminRegistrationView.as_view(), name="AdminRegistrationView"),
    path("User/Registration/", views.UserRegistrationView.as_view(), name="UserRegistrationView"),
    path('activate/<str:verification_link>/', views.ActivateAccountView.as_view(), name='activate_account'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
