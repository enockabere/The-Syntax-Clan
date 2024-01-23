import logging
import secrets
import string
from django.shortcuts import render, redirect
import requests
from django.contrib import messages
from cryptography.fernet import Fernet
from django.views import View
from myRequest.views import UserObjectMixins
import base64
import urllib.parse
import base64
from django.conf import settings as config
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from datetime import datetime


def get_object(endpoint):
    session = requests.Session()
    session.auth = config.AUTHS
    response = session.get(endpoint, timeout=10)
    return response


class Register(UserObjectMixins, View):
    def get(self, request):
        try:
            Access_Point = config.O_DATA.format("/QYCountries")
            response = get_object(Access_Point)
            ctx = {}
            if response.status_code == 200:
                cleanedData = response.json()
                resCountry = cleanedData["value"]
                ctx = {"country": resCountry}
        except Exception as e:
            print(e)
            messages.error(request, f"{e}")
            return redirect("Register")
        return render(request, "register.html", ctx)

    def post(self, request):
        try:
            lTRName = request.POST.get("lTRName")
            lTRMail = request.POST.get("lTRMail")
            phoneNumber = request.POST.get("phoneNumber")
            businessRegNo = request.POST.get("businessRegNo")
            postalAddress = request.POST.get("postalAddress")
            city = request.POST.get("city")
            Password = request.POST.get("Password")
            Password2 = request.POST.get("Password2")
            myAction = "insert"

            if len(Password) < 6:
                messages.error(request, "Password should be at least 6 characters")
                return redirect("Register")
            if Password != Password2:
                messages.error(request, "Password mismatch")
                return redirect("Register")

            if not businessRegNo:
                messages.error(
                    request, "Kindly provide your business registration number"
                )
                return redirect("Register")

            if not lTRMail:
                messages.error(request, "Kindly provide your email")
                return redirect("Register")

            if not lTRName:
                messages.error(request, "Kindly provide your LTR Name")
                return redirect("Register")

            nameChars = "".join(
                secrets.choice(string.ascii_uppercase + string.digits) for i in range(5)
            )
            verificationToken = str(nameChars)

            cipher_suite = Fernet(config.ENCRYPT_KEY)
            encrypted_text = cipher_suite.encrypt(Password.encode("ascii"))
            password = base64.urlsafe_b64encode(encrypted_text).decode("ascii")

            response = self.make_soap_request(
                "FnRegistrationSignup",
                lTRName,
                lTRMail,
                phoneNumber,
                postalAddress,
                businessRegNo,
                city,
                myAction,
                password,
                verificationToken,
            )
            if response != "False":
                email_subject = "Activate your account"
                email_template = f"Thanks for creating an account with us! </br> Please use the Secret Code below to verify your account.</br> <b>Secret Code:</b> {verificationToken}"

                send_verification_mail = self.make_soap_request(
                    "FnSendNotification",
                    email_subject,
                    lTRName,
                    lTRMail,
                    email_template,
                    response,
                )
                resend_data = {
                    "recipient_name": lTRName,
                    "email": lTRMail,
                    "token": verificationToken,
                    "user_id": response,
                }
                request.session["resend_data"] = resend_data

                if send_verification_mail == True:
                    messages.success(
                        request, "We sent you an email to verify your account"
                    )
                    return redirect("verify")
                messages.error(request, "Verification Email not sent")
                return redirect("Register")
            messages.error(request, f"{response}")
            return redirect("Register")
        except Exception as e:
            print(e)
            messages.error(request, f"{e}")
            return redirect("Register")


def verifyRequest(request):
    if request.method == "POST":
        try:
            email = request.POST.get("email")
            secret = request.POST.get("secret")
            verified = True
            Access_Point = config.O_DATA.format(
                f"/QYLTRLogins?$filter=LTR_Email%20eq%20%27{email}%27"
            )
            response = get_object(Access_Point)

            if response.status_code != 200:
                messages.error(
                    request, f"Failed with status code: {response.status_code}"
                )
                return redirect("Login")
            cleanedData = response.json()
            for res in cleanedData["value"]:
                if res["Verification_Token"] == secret:
                    response = config.CLIENT.service.FnVerified(verified, email)
                    messages.success(request, "Verification Successful")
                    return redirect("Login")
        except requests.exceptions.RequestException as e:
            print(e)
            messages.error(request, "Not Verified. check Credentials or Register")
            return redirect("verify")
        except ValueError:
            messages.error(request, "Wrong Input")
            return redirect("verify")
    return render(request, "verify.html")


def profile(request):
    try:
        userId = request.session["UserID"]
        LTR_Email = request.session["LTR_Email"]
        LTR_Name = request.session["LTR_Name"]
        Country = request.session["Country"]
        Business_Registration_No_ = request.session["Business_Registration_No_"]

        if request.method == "POST":
            ltrName = request.POST.get("ltrName")
            ltraddress = request.POST.get("ltraddress")
            ltrPhone = request.POST.get("ltrPhone")
            country = request.POST.get("country")
            myAction = "modify"

            try:
                response = config.CLIENT.service.UpdateAccountDetails(
                    userId, ltrName, ltraddress, ltrPhone, country, myAction
                )
                if response == True:
                    messages.success(request, "profile Updated successfully")
                    return redirect("profile")
                messages.error(request, response)
                return redirect("profile")

            except Exception as e:
                messages.error(request, e)
                print(e)
                return redirect("profile")
    except KeyError as e:
        messages.info(request, "Session Expired, Login Again")
        print(e)
        return redirect("login")

    ctx = {
        "userID": userId,
        # "No": No,
        "LTR_Name": LTR_Name,
        "Country": Country,
        "LTR_Email": LTR_Email,
        "Business_Registration_No_": Business_Registration_No_,
    }

    return render(request, "profile.html", ctx)


class Login(UserObjectMixins, View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        try:
            email = request.POST.get("email")
            password = request.POST.get("password")

            Access_Point = config.O_DATA.format(
                f"/QYLTRLogins?$filter=LTR_Email%20eq%20%27{email}%27"
            )
            response = get_object(Access_Point)
            if response.status_code == 200:
                cleanedData = response.json()

                for res in cleanedData["value"]:
                    if res["Verified"] == True:
                        Portal_Password = base64.urlsafe_b64decode(res["MyPassword"])
                        request.session["UserID"] = res["No"]
                        request.session["LTR_Name"] = res["LTR_Name"]
                        request.session["LTR_Email"] = res["LTR_Email"]
                        request.session["Country"] = res["Country"]
                        request.session["Business_Registration_No_"] = res[
                            "Business_Registration_No_"
                        ]

                        cipher_suite = Fernet(config.ENCRYPT_KEY)
                        decoded_text = cipher_suite.decrypt(Portal_Password).decode(
                            "ascii"
                        )

                        if decoded_text == password:
                            print("User ID:", request.session["UserID"])
                            saved_url = request.session.get("saved_url")
                            if saved_url is not None:
                                if "saved_url" in request.session:
                                    del request.session["saved_url"]
                                return HttpResponseRedirect(saved_url)
                            else:
                                return redirect("dashboard")
                        messages.error(request, "Invalid Password")
                        return redirect("Login")
                    messages.error(request, "Email not verified")
                    return redirect("Login")
                messages.error(request, "Email not registered")
                return redirect("Login")
        except Exception as e:
            messages.error(request, f"{e}")
            return redirect("Login")


class ResendEmail(UserObjectMixins, View):
    def post(self, request):
        try:
            resend_data = request.session["resend_data"]

            token = resend_data["token"]

            email_subject = "Activate your account"
            email_template = f"Thanks for creating an account with us! </br> Please use the Secret Code below to verify your account.</br> <b>Secret Code:</b> {token}"

            send_verification_mail = self.make_soap_request(
                "FnSendNotification",
                email_subject,
                resend_data["recipient_name"],
                resend_data["email"],
                email_template,
                resend_data["user_id"],
            )
            if send_verification_mail == True:
                messages.success(request, "We sent you an email to verify your account")
                return redirect("verify")
            messages.error(request, "Verification Email not sent")
            return redirect("verify")
        except Exception as e:
            print(e)
            messages.error(request, f"{e}")
            return redirect("verify")


class ResetPassword(UserObjectMixins, View):
    def post(self, request):
        try:
            email = request.POST.get("email")
        except ValueError:
            messages.error(request, "Missing Input")
            return redirect("Login")
        Access_Point = config.O_DATA.format(
            f"/QYLTRLogins?$filter=LTR_Email%20eq%20%27{email}%27"
        )
        try:
            response = get_object(Access_Point)

            if response.status_code != 200:
                messages.error(
                    request, f"Failed with status code: {response.status_code}"
                )
                return redirect("Login")
            cleanedData = response.json()

            for res in cleanedData["value"]:
                if res["LTR_Email"] == email:
                    request.session["resetMail"] = email
                    nameChars = "".join(
                        secrets.choice(string.ascii_uppercase + string.digits)
                        for i in range(5)
                    )
                    verificationToken = str(nameChars)

                    request.session["reset_token"] = verificationToken

                    email_subject = "Reset your Password"
                    email_template = f"Please use the Secret Code below to reset your password.</br> <b>Secret Code:</b> {verificationToken}"

                    send_verification_mail = self.make_soap_request(
                        "FnSendNotification",
                        email_subject,
                        res["LTR_Name"],
                        res["LTR_Email"],
                        email_template,
                        res["No"],
                    )
                    if send_verification_mail == True:
                        reset_data = {
                            "recipient_name": res["LTR_Name"],
                            "email": res["LTR_Email"],
                            "token": verificationToken,
                            "user_id": res["No"],
                        }
                        request.session["reset_data"] = reset_data
                        messages.success(
                            request, "We sent you an email to reset your password"
                        )
                        return redirect("reset")
                    messages.error(request, "Verification Email not sent")
                    return redirect("Login")
                else:
                    messages.error(request, "Invalid Email")
                    return redirect("Login")
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect("Login")


class reset_request(UserObjectMixins, View):
    def get(self, request):
        return render(request, "reset.html")

    def post(self, request):
        try:
            email = request.session["resetMail"]
            reset_token = request.session["reset_token"]
            password = request.POST.get("password")
            secret = request.POST.get("secret")
            password2 = request.POST.get("password2")
            verified = True
        except KeyError:
            messages.info(request, "Session Expired, Raise new password reset request")
            return redirect("Login")
        except ValueError:
            messages.error(request, "Invalid Input")
            return redirect("reset")
        if len(password) < 6:
            messages.error(request, "Password should be at least 6 characters")
            return redirect("reset")
        if password != password2:
            messages.error(request, "Password mismatch")
            return redirect("reset")

        if secret != reset_token:
            messages.error(request, "Invalid reset token")
            return redirect("reset")

        cipher_suite = Fernet(config.ENCRYPT_KEY)
        encrypted_text = cipher_suite.encrypt(password.encode("ascii"))
        myPassword = base64.urlsafe_b64encode(encrypted_text).decode("ascii")
        try:
            response = self.make_soap_request(
                "FnResetPassword", email, myPassword, verified
            )
            if response == True:
                messages.success(request, "Password Reset successful")
                del request.session["resetMail"]
                del request.session["reset_token"]
                del request.session["reset_data"]
                return redirect("Login")
            else:
                messages.error(request, "Error Try Again")
                return redirect("reset")
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect("reset")


class ResendResetToken(UserObjectMixins, View):
    def post(self, request):
        try:
            reset_data = request.session["reset_data"]

            token = reset_data["token"]

            email_subject = "Reset your Password"
            email_template = f"Please use the Secret Code below to reset your password.</br> <b>Secret Code:</b> {token}"

            send_verification_mail = self.make_soap_request(
                "FnSendNotification",
                email_subject,
                reset_data["recipient_name"],
                reset_data["email"],
                email_template,
                reset_data["user_id"],
            )
            if send_verification_mail == True:
                messages.success(request, "We sent you an email to verify your account")
                return redirect("reset")
            messages.error(request, "Verification Email not sent")
            return redirect("reset")
        except Exception as e:
            print(e)
            messages.error(request, f"{e}")
            return redirect("reset")


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
            )
            admin_user.save()
            validation_token = self.verificationToken(5)
            if validation_token:
                email_subject = "Activate your account"
                email_template = 'activate.html'
                recipient_name = first_name + " " + middle_name + " " + last_name
                recipient_email = email
                send_validation_email = self.send_mail(email_subject,email_template,recipient_name,recipient_email,validation_token)
                if send_validation_email == True:
                    messages.success(
                        request, "We sent you an email to verify your account"
                    )
                    return redirect("verify")
                messages.error(request, "Verification email failed, contact admin")
                self.logger.error(f"Verification email for {email} failed")
                return redirect("AdminRegistrationView")
            messages.error(request, "Verification token failed, contact admin")
            self.logger.error(f"Verification email for {email} failed")
            return redirect("AdminRegistrationView")
       
        except Exception as e:
            self.logger.error(f"{e}")
            messages.error(request, f"{e}")
            return redirect("AdminRegistrationView")

