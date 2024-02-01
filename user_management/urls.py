from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.AdminAllUsers.as_view(), name="admin_all_users"),
    path("edit-users/", views.AdminEditUsers.as_view(), name="admin_edit_users"),
    path("roles/", views.AdminRoles.as_view(), name="roles"),
    
]
