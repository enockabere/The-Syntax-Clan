from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("selfservice/", include("authentication.urls")),
    path("selfservice/", include("base.urls")),
    path("selfservice/", include("dashboard.urls")),
    path("selfservice/", include("pharmaceutical.urls")),
    path("selfservice/", include("vaccine.urls")),
    path("selfservice/", include("pesticide.urls")),
    path("selfservice/", include("feed.urls")),
    path("selfservice/", include("biocidal.urls")),
    path("selfservice/", include("devices.urls")),
    path("selfservice/", include("retention.urls")),
    path("selfservice/", include("permit.urls")),
    path("selfservice/", include("retailers.urls")),
    path("selfservice/", include("advertisement.urls")),
    path("selfservice/", include("disposal.urls")),
    path("selfservice/", include("manufacturing.urls")),
]
