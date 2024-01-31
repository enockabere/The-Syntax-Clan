import logging
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.views import View
from myRequest.views import UserObjectMixins
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from datetime import datetime
from django.utils import timezone
from .models import CustomUser
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from .models import PasswordResetRequest
from django.urls import reverse



class AdminRegistrationView(UserObjectMixins,View):
    template_name = 'admin_registration.html'
    logger = logging.getLogger('authentication')

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            middle_name = request.POST.get('middle_name')
            last_name = request.POST.get('last_name')
            password_confirm = request.POST.get('password_confirm')
            id_number = request.POST.get('id_number')
            agree = request.POST.get('agree')
            date_of_birth = datetime.strptime(
                    request.POST.get("date_of_birth"), "%Y-%m-%d"
                ).date()
            phone_number = request.POST.get('phone_number')
            

            if get_user_model().objects.filter(email=email).exists():
                self.logger.error("Email is already registered")
                messages.error(request, "Email is already registered")
                return redirect("AdminRegistrationView")
            
            if get_user_model().objects.filter(id_number=id_number).exists():
                self.logger.error("ID or Passport Number is already registered")
                messages.error(request, "ID or Passport Number is already registered")
                return redirect("AdminRegistrationView")
            
            if len(id_number) < 7 or len(id_number) > 9:
                self.logger.error("Invalid ID or Passport Number")
                messages.error(request, "Invalid ID or Passport Number")
                return redirect("AdminRegistrationView")
            
            if password != password_confirm:
                self.logger.error("Password Mismatch")
                messages.error(request, "Password Mismatch")
                return redirect("AdminRegistrationView")
            
            if not agree or agree == "":
                self.logger.error("Agree with the terms and conditions to continue")
                messages.error(request, "Agree with the terms and conditions to continue")
                return redirect("AdminRegistrationView")
            else:
                agree = eval(agree)
                
            today = datetime.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            
            if age < 18:
                self.logger.error("User must be at least 18 years old.")
                messages.error(request, "User must be at least 18 years old.")
                return redirect("AdminRegistrationView")
            
            if phone_number:
                if phone_number.startswith('0') and len(phone_number) == 10:
                    phone_number = phone_number.lstrip('0')
                    phone_number = f'254{phone_number}'
                    
                elif not phone_number.startswith('0') and len(phone_number) == 9:
                    phone_number = f'254{phone_number}'

                if len(phone_number) > 12:
                    messages.error(request, 'Phone number length cannot exceed 12 characters.')
                    return redirect("AdminRegistrationView")
            
            admin_user = get_user_model()(
                email=email,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                id_number=id_number,
                date_of_birth=date_of_birth,
                password=make_password(password),
                agree=agree,
                is_admin=True,  
                is_staff=True,
                is_superuser=True,
                phone_number = phone_number
            )
            admin_user.save()
            admin_group = Group.objects.get(name='Admin')
            normal_user_group = Group.objects.get(name='NormalUser')
            admin_user.groups.add(admin_group, normal_user_group)
            
            verification_link = get_random_string(length=32)
            admin_user.verification_link = verification_link
            admin_user.verification_link_created_at = timezone.now()
            admin_user.save()
            
            email_subject = "Activate your account"
            email_template = 'activate.html'
            recipient_name = f"{first_name} {middle_name} {last_name}"
            recipient_email = email
            verification_link = f"{request.scheme}://{request.get_host()}/selfservice/activate/{verification_link}/"
            send_validation_email = self.send_mail(email_subject,email_template,recipient_name,recipient_email,verification_link)
            if send_validation_email == True:
                messages.success(
                    request, "We sent you an email to verify your account"
                )
                return redirect("Login")
            messages.error(request, "Verification email failed, contact admin")
            self.logger.error(f"Verification email for {email} failed")
            return redirect("AdminRegistrationView")
       
        except Exception as e:
            self.logger.error(f"{e}")
            messages.error(request, f"{e}")
            return redirect("AdminRegistrationView")


class ActivateAccountView(UserObjectMixins,View):
    template_name = 'activate_account.html' 
    logger = logging.getLogger('authentication')

    def get(self, request, verification_link):
        try:
            user = CustomUser.objects.get(verification_link=verification_link)
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid verification link.")
            return redirect("Login")
        expiration_time = user.verification_link_created_at + timezone.timedelta(minutes=10)
        if timezone.now() > expiration_time:
            messages.error(request, "Verification link has expired.")
            return redirect("Login")
        user.is_email_verified = True
        user.save()

        messages.success(request, "Your account has been successfully activated. You can now log in.")
        return redirect("Login")

    def post(self, request, verification_link):
        try:
            user = CustomUser.objects.get(verification_link=verification_link)
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid verification link.")
            return redirect("Login")

        expiration_time = user.verification_link_created_at + timezone.timedelta(minutes=10)


        if timezone.now() > expiration_time:
            email_subject = "Activate your account"
            email_template = 'activate.html'
            recipient_name = f"{user.first_name} {user.middle_name} {user.last_name}"
            recipient_email = user.email
            resend_activation_email = self.send_mail(email_subject,email_template,recipient_name,recipient_email,user.verification_link)
            if resend_activation_email == True:
                messages.success(request, "A new activation email has been sent. Please check your inbox.")
                return redirect("Login")
            messages.error(request, "Verification email failed, contact admin")
            self.logger.error(f"Verification email for {user.email} failed")
            return redirect("activate_account", verification_link=user.verification_link)
        messages.error(request, "Verification link has not expired")
        return redirect("Login")
    
class UserRegistrationView(UserObjectMixins,View):
    template_name = 'user_registration.html'
    logger = logging.getLogger('authentication')

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            middle_name = request.POST.get('middle_name')
            last_name = request.POST.get('last_name')
            password_confirm = request.POST.get('password_confirm')
            id_number = request.POST.get('id_number')
            agree = request.POST.get('agree')
            date_of_birth = datetime.strptime(
                    request.POST.get("date_of_birth"), "%Y-%m-%d"
                ).date()
            
            phone_number = request.POST.get('phone_number')
            

            if get_user_model().objects.filter(email=email).exists():
                self.logger.error("Email is already registered")
                messages.error(request, "Email is already registered")
                return redirect("UserRegistrationView")
            
            if get_user_model().objects.filter(id_number=id_number).exists():
                self.logger.error("ID or Passport Number is already registered")
                messages.error(request, "ID or Passport Number is already registered")
                return redirect("UserRegistrationView")
            
            if len(id_number) < 7 or len(id_number) > 9:
                self.logger.error("Invalid ID or Passport Number")
                messages.error(request, "Invalid ID or Passport Number")
                return redirect("UserRegistrationView")
            
            if password != password_confirm:
                self.logger.error("Password Mismatch")
                messages.error(request, "Password Mismatch")
                return redirect("UserRegistrationView")
            
            if not agree or agree == "":
                self.logger.error("Agree with the terms and conditions to continue")
                messages.error(request, "Agree with the terms and conditions to continue")
                return redirect("UserRegistrationView")
            else:
                agree = eval(agree)
                
            today = datetime.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            
            if age < 18:
                self.logger.error("User must be at least 18 years old.")
                messages.error(request, "User must be at least 18 years old.")
                return redirect("UserRegistrationView")
            
            if phone_number:
                if phone_number.startswith('0') and len(phone_number) == 10:
                    phone_number = phone_number.lstrip('0')
                    phone_number = f'254{phone_number}'
                    
                elif not phone_number.startswith('0') and len(phone_number) == 9:
                    phone_number = f'254{phone_number}'

                if len(phone_number) > 12:
                    messages.error(request, 'Phone number length cannot exceed 12 characters.')
                    return redirect("UserRegistrationView")
            
            user = get_user_model()(
                email=email,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                id_number=id_number,
                date_of_birth=date_of_birth,
                password=make_password(password),
                agree=agree,
                is_admin=False,
                is_staff=True,
                is_superuser=True,
                phone_number = phone_number
            )
            user.save()    
            
            normal_user_group = Group.objects.get(name='NormalUser')
            user.groups.add(normal_user_group)    
               
            verification_link = get_random_string(length=32)
            user.verification_link = verification_link
            user.verification_link_created_at = timezone.now()
            user.save()
            
            email_subject = "Activate your account"
            email_template = 'activate.html'
            recipient_name = f"{first_name} {middle_name} {last_name}"
            recipient_email = email
            verification_link = f"{request.scheme}://{request.get_host()}/selfservice/activate/{verification_link}/"
            send_validation_email = self.send_mail(email_subject,email_template,recipient_name,recipient_email,verification_link)
            if send_validation_email == True:
                messages.success(
                    request, "We sent you an email to verify your account"
                )
                return redirect("Login")
            messages.error(request, "Verification email failed, contact admin")
            self.logger.error(f"Verification email for {email} failed")
            return redirect("UserRegistrationView")
       
        except Exception as e:
            self.logger.error(f"{e}")
            messages.error(request, f"{e}")
            return redirect("UserRegistrationView")
        
class Login(UserObjectMixins, View):
    template_name = 'login.html'
    logger = logging.getLogger('authentication')

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            id_number = request.POST.get('id_number')
            password = request.POST.get('password')
            remember = request.POST.get('remember')

            user = authenticate(request, id_number=id_number, password=password)

            if user is not None and user.is_active and user.is_email_verified:
                full_name = f"{user.first_name} {user.middle_name} {user.last_name}"
                request.session['user_full_name'] = full_name
                request.session['user_id_number'] = user.id_number
                request.session['user_email'] = user.email

                user_roles = list(user.groups.values_list('name', flat=True))
                request.session['user_roles'] = user_roles
                print(user_roles)

                login(request, user)

                if remember:
                    request.session.set_expiry(30 * 24 * 60 * 60)

                return redirect('dashboard')
            else:
                if user is not None and not user.is_active:
                    messages.error(request, 'Your account is not active. Please contact support.')
                    return redirect('Login')
                elif user is not None and not user.is_email_verified:
                    messages.error(request, 'Your email is not verified. Please check your inbox for the verification link.')
                    return redirect('Login')
                else:
                    messages.error(request, 'Invalid login credentials')
                return redirect('Login')
        except Exception as e:
            self.logger.error(f"{e}")
            messages.error(request, f"{e}")
            return redirect("Login")


class RequestPasswordResetView(UserObjectMixins,View):
    def post(self, request):
        email = request.POST.get('reset_email')
        user = get_user_model().objects.filter(email=email).first()

        if user:
            token = get_random_string(length=32)
            reset_request = PasswordResetRequest.objects.create(user=user, token=token)
            
            subject = 'Password Reset Request'
            recipient_name = f"{user.first_name} {user.middle_name} {user.last_name}"
            email_template = 'reset_mail.html'
            recipient_email = user.email
            verification_link = request.build_absolute_uri(reverse('password_reset_verification', args=[token]))

            send_validation_email = self.send_mail(subject,email_template,recipient_name,recipient_email,verification_link)
            if send_validation_email == True:
                messages.success(
                    request, "Password reset email sent. Check your inbox."
                )
                return redirect("Login")
            messages.error(request, "Email failed, contact admin")
            self.logger.error(f"Reset email for {email} failed")
            return redirect("Login")
        else:
            messages.error(request, 'Email not found.')
            return redirect("Login")
        
class PasswordResetVerificationView(View):
    template_name = 'password_reset_verification.html'
    logger = logging.getLogger('authentication')

    def get(self, request, token):
        reset_request = get_object_or_404(PasswordResetRequest, token=token)

        if not reset_request.is_verified:
            reset_request.is_verified = True
            reset_request.save()
            messages.success(request, "Link validated successfully")
            
            return redirect('set_new_password', token=token)
        else:
            messages.error(request, 'Invalid reset link')
            return redirect('Login')

        
class SetNewPasswordView(View):
    template_name = 'set_new_password.html'
    logger = logging.getLogger('authentication')
    def get(self, request, token):
        reset_request = get_object_or_404(PasswordResetRequest, token=token)
        ctx = {}

        if reset_request.is_verified:
            ctx = {"token":token}
            return render(request, self.template_name,ctx)
        else:
            messages.error(request, 'Invalid verification link.')
            return redirect('set_new_password', token=token)

    def post(self, request, token):
        reset_request = get_object_or_404(PasswordResetRequest, token=token)

        if reset_request.is_verified:
            password = request.POST.get('password')
            confirm_password = request.POST.get('password_confirm')
            
            if len(password) < 6:
                self.logger.error("Password Too Short")
                messages.error(request, "Password Too Short")
                return redirect("set_new_password")
            
            if password != confirm_password:
                self.logger.error("Password Mismatch")
                messages.error(request, "Password Mismatch")
                return redirect("set_new_password")
        
            user = reset_request.user
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successfully. You can now log in with your new password.')
            return redirect('Login')
        else:
            messages.error(request, 'Invalid verification link.')
            self.logger.error("Invalid verification link.")
            return redirect('Login')
            
class LogoutView(View):
    logger = logging.getLogger('authentication')
    def get(self, request):
        request.session.flush()
        logout(request)
        return redirect('Login')