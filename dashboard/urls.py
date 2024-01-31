from django.urls import path
from . import views

urlpatterns = [
    path("Dashboard/", views.Dashboard.as_view(), name="dashboard"),
]
