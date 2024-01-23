import base64
import logging
import os
from django.shortcuts import render, redirect
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
class ManufacturingLicense(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task_get_permits = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QyManufacturingLicence", "UserCode", "eq", userID
                    )
                )
                task_get_countries = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYCountries")
                )

                response = await asyncio.gather(task_get_permits, task_get_countries)

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
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "country": resCountry,
        }
        return render(request, "manufacture.html", ctx)

    async def post(self, request):
        try:
            manufacturingNo = request.POST.get("manufacturingNo")
            directPersonalSupervisor = request.POST.get("directPersonalSupervisor")
            supervisorQualifications = request.POST.get("supervisorQualifications")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            iAgree = eval(request.POST.get("iAgree"))
            myAction = request.POST.get("myAction")
            plotNo = request.POST.get("plotNo")
            name = request.POST.get("name")
            professionalRegNo = request.POST.get("professionalRegNo")
            email = request.POST.get("email")
            cellPhone = request.POST.get("cellPhone")
            iDorPassportOrAlienIDNo = request.POST.get("iDorPassportOrAlienIDNo")
            nationality = request.POST.get("nationality")

            if not iAgree:
                iAgree = False

            response = self.make_soap_request(
                "FnManufacturingLicenceCard",
                manufacturingNo,
                directPersonalSupervisor,
                supervisorQualifications,
                iAgree,
                userCode,
                myAction,
                plotNo,
                name,
                professionalRegNo,
                email,
                cellPhone,
                iDorPassportOrAlienIDNo,
                nationality,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != "0" and response is not None and response != "":
                    messages.success(request, "Success")
                    return redirect("ManufacturingLicenseDetails", pk=response)
                else:
                    messages.error(request, f"{response}")
                    return redirect("ManufacturingLicense")
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("ManufacturingLicense")


class ManufacturingApplications(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task_get_manufacturing = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QyManufacturingLicence", "UserCode", "eq", userID
                    )
                )
                response = await asyncio.gather(task_get_manufacturing)
                new_manufacturing = [
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
            "new_manufacturing": new_manufacturing,
            "submitted": submitted,
        }
        return render(request, "all_apps.html", ctx)


class ManufacturingLicenseDetails(UserObjectMixins, View):
    async def get(self, request, pk):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")
            permit = {}

            current_url = request.get_full_path()
            request.session["saved_url"] = current_url

            async with aiohttp.ClientSession() as session:
                task_get_permit = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyManufacturingLicence",
                        "ManufacturingNo",
                        "eq",
                        pk,
                    )
                )
                task_get_product = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QYRegistration",
                        "User_code",
                        "eq",
                        userID,
                    )
                )
                task4 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyManufacturingLicenceLines",
                        "ManufacturingNo",
                        "eq",
                        pk,
                    )
                )
                task5 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYDocumentAttachments", "No_", "eq", pk
                    )
                )
                task_get_countries = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYCountries")
                )
                response = await asyncio.gather(
                    task_get_permit, task_get_product, task4, task5, task_get_countries
                )
                for permit in response[0]:
                    if permit["UserCode"] == userID:
                        permit = permit
                approved_products = [
                    x for x in response[1] if x["Status"] == "Approved"
                ]
                lines = [x for x in response[2]]
                attachments = [x for x in response[3]]
                resCountry = [x for x in response[4]]
        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        ctx = {
            "permit": permit,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "approved_products": approved_products,
            "lines": lines,
            "attachments": attachments,
            "country": resCountry,
        }
        return render(request, "manufacture-detail.html", ctx)

    async def post(self, request, pk):
        try:
            myAction = request.POST.get("myAction")
            lineNo = request.POST.get("lineNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            productNo = request.POST.get("productNo")
            response = self.make_soap_request(
                "FnManufacturingLcenecLines",
                pk,
                lineNo,
                productNo,
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
                    return redirect("ManufacturingLicenseDetails", pk=pk)
                else:
                    messages.error(request, f"{response}")
                    return redirect("ManufacturingLicenseDetails", pk=pk)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("ManufacturingLicenseDetails", pk=pk)


class ManufacturingLicenseLines(UserObjectMixins, View):
    def get(self, request, pk):
        try:
            PermitLines = self.one_filter(
                "/QyManufacturingLicenceLines",
                "ManufacturingNo",
                "eq",
                pk,
            )

            return JsonResponse(PermitLines, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class ManufacturingLicenseCustomer(UserObjectMixins, View):
    async def post(self, request):
        try:
            manufacturingNo = request.POST.get("manufacturingNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")

            response = self.make_soap_request(
                "FnManufacturingLicencePayment",
                manufacturingNo,
                userCode,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, "Success")
                    return redirect("ManufacturingLicenseDetails", pk=manufacturingNo)
                else:
                    messages.error(request, f"{response}")
                    return redirect("ManufacturingLicenseDetails", pk=manufacturingNo)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("ManufacturingLicenseDetails", pk=manufacturingNo)


class ManufacturingLicenseInvoice(UserObjectMixins, View):
    def post(self, request):
        try:
            manufacturingNo = request.POST.get("manufacturingNo")
            filenameFromApp = "invoice_" + manufacturingNo + ".pdf"
            invoice_number = None
            invoices = self.one_filter(
                "/QySalesInvoiceHeader",
                "ExternalDocumentNo",
                "eq",
                manufacturingNo,
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
            return redirect("ManufacturingLicenseDetails", pk=manufacturingNo)


class ManufacturingLicenseAttachments(UserObjectMixins, View):
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
            tableID = 50046
            fileName = request.POST.get("attachmentCode")
            response = False

            _, file_extension = os.path.splitext(attachment.name)
            fileName_with_extension = f"{fileName}{file_extension}"
            attachment_data = base64.b64encode(attachment.read())

            response = self.make_soap_request(
                "FnAttachementManufacturingLicence",
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


class SubmitManufacturingLicense(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            userCode = request.session["UserID"]

            response = self.make_soap_request("FnSubmitManufacturing", pk, userCode)

            if response == True:
                return JsonResponse({"response": str(response)}, safe=False)
            return JsonResponse({"error": str(response)}, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class ManufacturingLicenseCert(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Manufacturing_License_Cert_" + pk + ".pdf"
            response = self.make_soap_request(
                "PrintManufacturingLicenceCertificate", pk
            )
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
            return redirect("ManufacturingLicenseDetails", pk=pk)
