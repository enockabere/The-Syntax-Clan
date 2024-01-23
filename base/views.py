import asyncio
import aiohttp
from django.contrib import messages
from django.shortcuts import render, redirect
from django.shortcuts import redirect
from django.views import View
import base64
import hashlib
import hmac
from django.conf import settings as config
from django.http import JsonResponse
import requests
from myRequest.views import UserObjectMixins
from asgiref.sync import sync_to_async


# Create your views here.
def sidebar(request):
    return render(request, "sidebar.html")


def profileRequest(request):
    try:
        userID = request.session["UserID"]
        LTR_Name = request.session["LTR_Name"]
        LTR_Email = request.session["LTR_Email"]
        Country = request.session["Country"]
        Business_Registration_No_ = request.session["Business_Registration_No_"]
    except KeyError as e:
        messages.error(request, e)
        return redirect("login")
    ctx = {
        "userID": userID,
        "LTR_Name": LTR_Name,
        "Country": Country,
        "LTR_Email": LTR_Email,
        "Business_Registration_No_": Business_Registration_No_,
    }
    return render(request, "profile.html", ctx)


def contact(request):
    return render(request, "contact.html")


def FAQRequest(request):
    try:
        LTR_Name = request.session["LTR_Name"]
        LTR_Email = request.session["LTR_Email"]
    except KeyError as e:
        messages.error(request, e)
        return redirect("login")
    ctx = {"LTR_Name": LTR_Name, "LTR_Email": LTR_Email}
    return render(request, "faq.html", ctx)


def Manual(request):
    try:
        LTR_Name = request.session["LTR_Name"]
        LTR_Email = request.session["LTR_Email"]
    except KeyError as e:
        messages.error(request, e)
        return redirect("login")
    ctx = {"LTR_Name": LTR_Name, "LTR_Email": LTR_Email}
    return render(request, "manual.html", ctx)


class PesaflowPaymentView(View):
    def post(self, request):
        try:
            user_data = request.session["user_data"]
            api_client_id = config.PESAFLOW_CLIENT_ID
            bill_desc = request.POST.get("bill_desc")
            currency = request.POST.get("currency")
            bill_ref_number = request.POST.get("bill_ref_number")
            client_msisdn = user_data["mobile_number"]
            client_name = request.POST.get("client_name")
            client_id_number = user_data["id_number"]
            client_email = user_data["email"]
            callback_url = config.REDIRECT_URI
            amount_expected = request.POST.get("amount_expected")
            notification_url = config.NOTIFICATION_URL
            client_picture_url = "https://pixabay.com/illustrations/avatar-icon-placeholder-facebook-1968236/"
            checkout_format = "json"
            send_stk_push = "true"
            secret_key = config.PESAFLOW_CLIENT_SECRET

            Process = request.POST.get("Process")
            Veterinary_Classes = request.POST.get("Veterinary_Classes")
            Types_Of_Manufacturers = request.POST.get("Types_Of_Manufacturers")
            service_code_mapping = {
                ("REGISTRATION", "VETERINARY PHARMACEUTICAL", "Local"): "5098985",
                ("REGISTRATION", "VETERINARY PHARMACEUTICAL", "Foreign"): "5098644",
                ("REGISTRATION", "VETERINARY PESTICIDE", "Local"): "5099080",
                ("REGISTRATION", "VETERINARY PESTICIDE", "Foreign"): "5098722",
                ("REGISTRATION", "VETERINARY VACCINE", "Local"): "5099202",
                ("REGISTRATION", "VETERINARY VACCINE", "Foreign"): "5098856",
                ("RETENTION", "VETERINARY PHARMACEUTICAL", "None"): "5099389",
                ("RETENTION", "VETERINARY PESTICIDE", "None"): "5099476",
                ("RETENTION", "VETERINARY VACCINE", "None"): "5099554",
                ("INSPECTORATE", "WHOLESALE PREMISE PERMIT", "Local"): "4316760",
                ("INSPECTORATE", "RETAIL PREMISE PERMIT", "Local"): "4316462",
                ("INSPECTORATE", "MANUFACTURING PERMIT", "Local"): "4316394",
                ("INSPECTORATE", "ADVERTISING PERMIT", "Local"): "4316326",
                ("GMP", "GMP", "Local"): "",
                ("GMP", "GMP", "Foreign"): "5098337",
            }

            service_code = service_code_mapping.get(
                (Process, Veterinary_Classes, Types_Of_Manufacturers), None
            )

            data_string = (
                api_client_id
                + amount_expected
                + service_code
                + client_id_number
                + currency
                + bill_ref_number
                + bill_desc
                + client_name
                + secret_key
            )

            key = config.KEY
            hash_hexdigest = hmac.new(
                key.encode("utf-8"), data_string.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            sample_string = hash_hexdigest
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            base64_string = base64_bytes.decode("ascii")

            data = {
                "apiClientID": api_client_id,
                "serviceID": service_code,
                "billDesc": bill_desc,
                "currency": currency,
                "billRefNumber": bill_ref_number,
                "clientMSISDN": client_msisdn,
                "clientName": client_name,
                "clientIDNumber": client_id_number,
                "clientEmail": client_email,
                "callBackURLOnSuccess": callback_url,
                "amountExpected": amount_expected,
                "notificationURL": notification_url,
                "secureHash": base64_string,
                "format": checkout_format,
                "sendSTK": send_stk_push,
                "pictureURL": client_picture_url,
            }

            api_url = config.API_URL
            response = requests.post(api_url, json=data)

            if response.status_code == 200:
                response_data = response.json()
                return JsonResponse(
                    {
                        "response_data": response_data,
                    },
                    safe=False,
                )
            else:
                return JsonResponse(
                    {
                        "response_data": response.json(),
                        "status_code": response.status_code,
                        "user_data": user_data,
                        "mobile_number": client_msisdn,
                    },
                    safe=False,
                )
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class GetCountries(UserObjectMixins, View):
    async def get(self, request):
        try:
            async with aiohttp.ClientSession() as session:
                task_get_countries = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYCountries")
                )
                response = await asyncio.gather(task_get_countries)

                resCountry = [x for x in response[0]]
                return JsonResponse(resCountry, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse(f"{e}", safe=False)


class GetProducts(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            async with aiohttp.ClientSession() as session:
                task_get_product = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QYRegistration",
                        "User_code",
                        "eq",
                        userID,
                    )
                )
                response = await asyncio.gather(task_get_product)

                Products = [x for x in response[0]]
                return JsonResponse(Products, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse(f"{e}", safe=False)
