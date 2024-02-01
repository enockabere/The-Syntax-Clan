from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from myRequest.views import UserObjectMixins
import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from authentication.models import CustomUser
from django.contrib.auth.models import Group

class AdminAllUsers(UserObjectMixins, View):
    template_name = 'users.html'
    logger = logging.getLogger('admin_users')
    
    @method_decorator(login_required(login_url='Login')) 
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            user_data = request.session["user_data"]
            
            all_users = CustomUser.objects.all()
            roles = Group.objects.all()

            ctx = {
                "user_data": user_data,
                "all_users": all_users,
                "roles":roles
            }
        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("dashboard")
        return render(request, self.template_name, ctx)
    
class AdminEditUsers(UserObjectMixins, View):
    def post(self, request):
        try:
            user_id = request.POST.get('user_id')
            is_staff = request.POST.get('is_staff')
            is_superuser = request.POST.get('is_superuser')
            is_admin = request.POST.get('is_admin')
            is_active = request.POST.get('is_active')

            is_staff = is_staff.lower() == "true" if is_staff else False
            is_superuser = is_superuser.lower() == "true" if is_superuser else False
            is_admin = is_admin.lower() == "true" if is_admin else False
            is_active = is_active.lower() == "true" if is_active else False

            if user_id and user_id.isdigit():
                user_to_edit = CustomUser.objects.get(id=user_id)
                user_to_edit.is_staff = is_staff
                user_to_edit.is_superuser = is_superuser
                user_to_edit.is_admin = is_admin
                user_to_edit.is_active = is_active

                user_to_edit.save()
                messages.success(request, 'User details updated successfully.')
                return redirect("admin_all_users")
            else:
                messages.error(request, 'Invalid user ID.')
                return redirect("admin_all_users")

        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect("admin_all_users")
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect("admin_all_users")


class AdminRoles(UserObjectMixins, View):
    template_name = 'roles.html'
    logger = logging.getLogger('admin_users')
    
    @method_decorator(login_required(login_url='Login')) 
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            user_data = request.session["user_data"]
            
            all_roles = Group.objects.all()
            
            user = CustomUser.objects.get(id=user_data.user_id)
            
            user_roles = user.groups.all()

            ctx = {
                "user_data": user_data,
                "all_roles": all_roles,
                "user_roles": user_roles,
            }
        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("dashboard")
        return render(request, self.template_name, ctx)
    def post(self, request):
        try:
            role_name = request.POST.get('role_name')

            if role_name:
                new_role, created = Group.objects.get_or_create(name=role_name)

                if created:
                    messages.success(request, f'Role "{role_name}" added successfully.')
                    return redirect("roles")
                else:
                    messages.warning(request, f'Role "{role_name}" already exists.')
                    return redirect("roles")
            else:
                messages.error(request, 'Role name cannot be empty.')
                return redirect("roles")

        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("roles")
        

class AdminEditRoles(UserObjectMixins, View):
    def post(self, request):
        try:
            role_id = request.POST.get('role_id')
            role_name = request.POST.get('role_name')

            if role_id and role_id.isdigit():
                role_to_edit = Group.objects.get(id=role_id)
                role_to_edit.name = role_name
                role_to_edit.save()
                
                messages.success(request, 'Updated successfully.')
                return redirect("roles")
            else:
                messages.error(request, 'Invalid Role ID.')
                return redirect("roles")

        except Group.DoesNotExist:
            messages.error(request, 'Role not found.')
            return redirect("roles")
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect("roles")

class AdminAssignRoleToUser(UserObjectMixins, View):
    def post(self, request):
        try:
            role_id = request.POST.get('role_id')
            user_id = request.POST.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            role = Group.objects.get(id=role_id)
            
            user.groups.add(role)
            messages.success(request, 'Role assigned successfully.')
            return redirect("admin_all_users")

        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect("admin_all_users")
        except Group.DoesNotExist:
            messages.error(request, 'Role not found.')
            return redirect("admin_all_users")
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect("admin_all_users")
        
class AdminRemoveRoleFromUser(UserObjectMixins, View):
    def post(self, request):
        try:
            role_id = request.POST.get('role_id')
            user_id = request.POST.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            
            if role_id and role_id.isdigit():
                role_to_remove = Group.objects.get(id=role_id)
                user.groups.remove(role_to_remove)
                messages.success(request, 'Role removed successfully.')
                return redirect('admin_all_users')
            else:
                messages.error(request, 'Invalid Role ID.')
                return redirect('admin_all_users')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect("admin_all_users")
        except Group.DoesNotExist:
            messages.error(request, 'Role not found.')
            return redirect("admin_all_users")
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect("admin_all_users")