from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("selfservice/", include("authentication.urls")),
    path("selfservice/", include("base.urls")),
    path("selfservice/", include("dashboard.urls")),
    path("selfservice/", include("savings.urls")),
    path("selfservice/", include("vaccine.urls")),
    path("selfservice/", include("pesticide.urls")),
    path("selfservice/", include("retention.urls")),
    path("selfservice/", include("manufacturing.urls")),
    path("selfservice/", include("user_management.urls")),
]
