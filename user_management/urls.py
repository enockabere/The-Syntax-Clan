from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.AdminAllUsers.as_view(), name="admin_all_users"),
    path("edit-users/", views.AdminEditUsers.as_view(), name="admin_edit_users"),
    path("roles/", views.AdminRoles.as_view(), name="roles"),
    path("edit-roles/", views.AdminEditRoles.as_view(), name="admin_edit_roles"),
    path("assign-roles/", views.AdminAssignRoleToUser.as_view(), name="admin_assign_role"),
    path("remove-roles/", views.AdminRemoveRoleFromUser.as_view(), name="admin_remove_role"),
]
