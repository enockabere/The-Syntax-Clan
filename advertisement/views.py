import base64
import logging
import os
from django.shortcuts import render, redirect
import requests
import json
from django.conf import settings as config
from django.contrib import messages
from django.views import View
import io as BytesIO
from django.http import HttpResponse, JsonResponse
from myRequest.views import UserObjectMixins
from asgiref.sync import sync_to_async
import asyncio
import aiohttp


# Create your views here.
class Advertisement(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QyAdvertisement", "UserCode", "eq", userID
                    )
                )
                task_get_countries = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYCountries")
                )

                response = await asyncio.gather(task, task_get_countries)

                permits = [x for x in response[0]]
                Approved = [x for x in response[0] if x["Status"] == "Approved"]

                resCountry = [x for x in response[1]]

        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse(permits, safe=False)

        ctx = {
            "approved": Approved,
            "country": resCountry,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
        }
        return render(request, "advertise.html", ctx)

    async def post(self, request):
        try:
            advertisementNo = request.POST.get("advertisementNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            formOfAdvertisement = request.POST.get("formOfAdvertisement")
            myAction = request.POST.get("myAction")

            response = self.make_soap_request(
                "FnAdvartisementCard",
                advertisementNo,
                formOfAdvertisement,
                userCode,
                myAction,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != "0" and response is not None and response != "":
                    messages.success(request, "Success")
                    return redirect("AdvertiseDetails", pk=response)
                else:
                    messages.error(request, f"{response}")
                    return redirect("advertise")
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("advertise")


class MyAdverts(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task_get_advertisement = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QyAdvertisement", "UserCode", "eq", userID
                    )
                )
                response = await asyncio.gather(task_get_advertisement)
                new_advertisement = [
                    x for x in response[0] if x["Document_Stage"] == "Not Submitted"
                ]
                submitted = [
                    x for x in response[0] if x["Document_Stage"] == "Submitted"
                ]

        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        ctx = {
            "userID": userID,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "new_advertisement": new_advertisement,
            "submitted": submitted,
        }
        return render(request, "my_adverts.html", ctx)


class AdvertiseDetails(UserObjectMixins, View):
    async def get(self, request, pk):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")
            res = {}

            async with aiohttp.ClientSession() as session:
                task = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QyAdvertisement", "AdvartisementNo", "eq", pk
                    )
                )
                task_get_countries = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYCountries")
                )
                task3 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYRegistration", "User_code", "eq", userID
                    )
                )
                task4 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyAdvertisementLines",
                        "AdvartisementNo",
                        "eq",
                        pk,
                    )
                )
                task5 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYDocumentAttachments", "No_", "eq", pk
                    )
                )
                response = await asyncio.gather(
                    task, task_get_countries, task3, task4, task5
                )
                for task in response[0]:
                    if task["UserCode"] == userID:
                        res = task
                resCountry = [x for x in response[1]]
                product = [x for x in response[2] if x["Status"] == "Approved"]
                lines = [x for x in response[3]]
                attachments = [x for x in response[4]]
        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse(res, safe=False)

        ctx = {
            "permit": res,
            "country": resCountry,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "product": product,
            "lines": lines,
            "attachments": attachments,
        }
        return render(request, "advertise-detail.html", ctx)

    async def post(self, request, pk):
        try:
            lineNo = request.POST.get("lineNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            product = request.POST.get("product")
            targetAudience = request.POST.get("targetAudience")
            uses = request.POST.get("uses")
            myAction = request.POST.get("myAction")

            response = self.make_soap_request(
                "FnAdvartisementLines",
                pk,
                lineNo,
                product,
                targetAudience,
                uses,
                userCode,
                myAction,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, "Success")
                    return redirect("AdvertiseDetails", pk=pk)
                else:
                    messages.error(request, f"{response}")
                    return redirect("AdvertiseDetails", pk=pk)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("AdvertiseDetails", pk=pk)


class AdvertisementLines(UserObjectMixins, View):
    def get(self, request, pk):
        try:
            PermitLines = self.one_filter(
                "/QyAdvertisementLines",
                "AdvartisementNo",
                "eq",
                pk,
            )

            return JsonResponse(PermitLines, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class AdvertisingCustomer(UserObjectMixins, View):
    async def post(self, request):
        try:
            advartisementNo = request.POST.get("advartisementNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")

            response = self.make_soap_request(
                "FnAdvartisementPayment",
                advartisementNo,
                userCode,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, "Success")
                    return redirect("AdvertiseDetails", pk=advartisementNo)
                else:
                    messages.error(request, f"{response}")
                    return redirect("AdvertiseDetails", pk=advartisementNo)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("AdvertiseDetails", pk=advartisementNo)


class AdvertAttachments(UserObjectMixins, View):
    async def get(self, request, pk):
        try:
            Attachments = []
            async with aiohttp.ClientSession() as session:
                task_get_attachments = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYDocumentAttachments", "No_", "eq", pk
                    )
                )
                response = await asyncio.gather(task_get_attachments)

                Attachments = [x for x in response[0]]
                return JsonResponse(Attachments, safe=False)

        except Exception as e:
            logging.exception(e)
            return JsonResponse({"error": str(e)}, safe=False)

    async def post(self, request, pk):
        try:
            attachment = request.FILES.get("attachment")
            tableID = 50045
            fileName = request.POST.get("attachmentCode")
            response = False

            _, file_extension = os.path.splitext(attachment.name)
            fileName_with_extension = f"{fileName}{file_extension}"
            attachment_data = base64.b64encode(attachment.read())

            response = self.make_soap_request(
                "FnAttachementAdvartisement",
                pk,
                fileName_with_extension,
                attachment_data,
                tableID,
            )
            if response == True:
                message = "Attachment uploaded successfully"
                return JsonResponse({"success": True, "message": message})
            error = "Upload failed: {}".format(response)
            return JsonResponse({"success": False, "error": error})
        except Exception as e:
            error = "Upload failed: {}".format(e)
            logging.exception(e)
            return JsonResponse({"success": False, "error": error})


class AdvertisingInvoice(UserObjectMixins, View):
    def post(self, request):
        try:
            advartisementNo = request.POST.get("advartisementNo")
            filenameFromApp = "invoice_" + advartisementNo + ".pdf"
            invoice_number = None
            invoices = self.one_filter(
                "/QySalesInvoiceHeader",
                "ExternalDocumentNo",
                "eq",
                advartisementNo,
            )

            for number in invoices[1]:
                invoice_number = number["No"]

            response = self.make_soap_request("FnGenerateSalesInvoice", invoice_number)

            buffer = BytesIO.BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            responses = HttpResponse(
                buffer.getvalue(),
                content_type="application/pdf",
            )
            responses["Content-Disposition"] = f"inline;filename={filenameFromApp}"
            return responses
        except Exception as e:
            messages.error(request, f"Failed, {e}")
            logging.exception(e)
            return redirect("AdvertiseDetails", pk=advartisementNo)


class SubmitAdvert(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            userCode = request.session["UserID"]

            response = self.make_soap_request("FnSubmitAdvertisement", pk, userCode)

            if response == True:
                return JsonResponse({"response": str(response)}, safe=False)
            return JsonResponse({"error": str(response)}, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class AdvertCert(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Advertising_Cert_" + pk + ".pdf"
            response = self.make_soap_request("PrintAdvertisemntCertificate", pk)
            buffer = BytesIO.BytesIO()
            content = base64.b64decode(response)
            buffer.write(content)
            responses = HttpResponse(
                buffer.getvalue(),
                content_type="application/pdf",
            )
            responses["Content-Disposition"] = f"inline;filename={filenameFromApp}"
            return responses
        except Exception as e:
            messages.error(request, f"Failed, {e}")
            logging.exception(e)
            return redirect("AdvertiseDetails", pk=pk)
