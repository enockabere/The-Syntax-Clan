from django.urls import path

from . import views

urlpatterns = [
    path(
        "payment/gateway/<str:pk>",
        views.PaymentGateway.as_view(),
        name="PaymentGateway",
    ),
    path(
        "GenerateInvoice/<str:pk>",
        views.FNGenerateInvoice.as_view(),
        name="FNGenerateInvoice",
    ),
]
