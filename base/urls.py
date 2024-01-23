from django.urls import path
from . import views

urlpatterns = [
    path("sidebar", views.sidebar, name="sidebar"),
    path("profile", views.profileRequest, name="profile"),
    path("contact", views.contact, name="contact"),
    path("faq", views.FAQRequest, name="faq"),
    path("Manual", views.Manual, name="Manual"),
    path(
        "PesaflowPaymentView/",
        views.PesaflowPaymentView.as_view(),
        name="PesaflowPaymentView",
    ),
    path("GetCountries/", views.GetCountries.as_view(), name="GetCountries"),
    path("GetProducts/", views.GetProducts.as_view(), name="GetProducts"),
]
