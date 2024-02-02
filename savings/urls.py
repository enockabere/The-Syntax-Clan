from django.urls import path
from . import views

urlpatterns = [
    path("admin-account-types/", views.AccountTypes.as_view(), name="admin_account_types"),
    path("admin-transactions-test/", views.TransactionsTest.as_view(), name="admin_transactions_test"),
]
