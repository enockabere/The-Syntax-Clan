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
class Disposal(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QyDisposalRequest", "UserCode", "eq", userID
                    )
                )
                response = await asyncio.gather(task)

                permits = [x for x in response[0]]
                Approved = [x for x in response[0] if x["Status"] == "Approved"]

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
        }
        return render(request, "disposal.html", ctx)

    async def post(self, request):
        try:
            disposalNo = request.POST.get("disposalNo")
            nameOfTheDestructionCompany = request.POST.get(
                "nameOfTheDestructionCompany"
            )
            placeOfDisposal = request.POST.get("placeOfDisposal")
            wasteDescription = request.POST.get("wasteDescription")
            reason = request.POST.get("reason")
            iAgree = eval(request.POST.get("iAgree"))
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            myAction = request.POST.get("myAction")
            if not iAgree:
                iAgree = False

            response = self.make_soap_request(
                "FnDisposalRequestCard",
                disposalNo,
                iAgree,
                nameOfTheDestructionCompany,
                placeOfDisposal,
                userCode,
                myAction,
                wasteDescription,
                reason,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != "0" and response is not None and response != "":
                    messages.success(request, "Success")
                    return redirect("DisposalDetails", pk=response)
                else:
                    messages.error(request, f"{response}")
                    return redirect("Disposal")
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("Disposal")


class DisposalApplications(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task_get_disposal = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QyDisposalRequest", "UserCode", "eq", userID
                    )
                )
                response = await asyncio.gather(task_get_disposal)
                new_disposal = [
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
            "new_disposal": new_disposal,
            "submitted": submitted,
        }
        return render(request, "disposal_applications.html", ctx)


class DisposalDetails(UserObjectMixins, View):
    async def get(self, request, pk):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")
            res = {}

            async with aiohttp.ClientSession() as session:
                task = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyDisposalRequest",
                        "DisposalNo",
                        "eq",
                        pk,
                    )
                )
                task2 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYRegistration", "User_code", "eq", userID
                    )
                )
                task4 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyDisposalRequestLine",
                        "DisposalNo",
                        "eq",
                        pk,
                    )
                )
                task5 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYDocumentAttachments", "No_", "eq", pk
                    )
                )
                response = await asyncio.gather(task, task2, task4, task5)
                for task in response[0]:
                    if task["UserCode"] == userID:
                        res = task
                product = [x for x in response[1] if x["Status"] == "Approved"]
                lines = [x for x in response[2]]
                attachments = [x for x in response[3]]
        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse(res, safe=False)

        ctx = {
            "permit": res,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "product": product,
            "lines": lines,
            "attachments": attachments,
        }
        return render(request, "disposal-detail.html", ctx)

    async def post(self, request, pk):
        try:
            myAction = request.POST.get("myAction")
            lineNo = request.POST.get("lineNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            batchNo = request.POST.get("batchNo")
            product = request.POST.get("product")
            quantity = request.POST.get("quantity")
            reasonForDestruction = int(request.POST.get("reasonForDestruction"))
            Other_Reason = request.POST.get("Other_Reason")
            product_disposal_status = eval(request.POST.get("product_disposal_status"))
            Waste_Description = request.POST.get("Waste_Description")

            if not product:
                product = ""

            if not batchNo:
                batchNo = "None"

            if not Other_Reason:
                Other_Reason = "None"

            if not Waste_Description:
                Waste_Description = "None"

            response = self.make_soap_request(
                "FnDisposalRequestLines",
                pk,
                product,
                batchNo,
                quantity,
                reasonForDestruction,
                myAction,
                lineNo,
                userCode,
                Other_Reason,
                Waste_Description,
                product_disposal_status,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, "Success")
                    return redirect("DisposalDetails", pk=pk)
                else:
                    messages.error(request, f"{response}")
                    return redirect("DisposalDetails", pk=pk)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("DisposalDetails", pk=pk)


class DisposalLines(UserObjectMixins, View):
    def get(self, request, pk):
        try:
            PermitLines = self.one_filter(
                "/QyDisposalRequestLine",
                "DisposalNo",
                "eq",
                pk,
            )

            return JsonResponse(PermitLines, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class DisposalCustomer(UserObjectMixins, View):
    async def post(self, request):
        try:
            disposalNo = request.POST.get("disposalNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")

            response = self.make_soap_request(
                "FnDisposalRequestPayment",
                disposalNo,
                userCode,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, "Success")
                    return redirect("DisposalDetails", pk=disposalNo)
                else:
                    messages.error(request, f"{response}")
                    return redirect("DisposalDetails", pk=disposalNo)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("DisposalDetails", pk=disposalNo)


class DisposalAttachments(UserObjectMixins, View):
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
            tableID = 50053
            fileName = request.POST.get("attachmentCode")
            response = False

            _, file_extension = os.path.splitext(attachment.name)
            fileName_with_extension = f"{fileName}{file_extension}"
            attachment_data = base64.b64encode(attachment.read())

            response = self.make_soap_request(
                "FnAttachementDisposalRequest",
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


class DisposalInvoice(UserObjectMixins, View):
    def post(self, request):
        try:
            disposalNo = request.POST.get("disposalNo")
            filenameFromApp = "invoice_" + disposalNo + ".pdf"
            invoice_number = None
            invoices = self.one_filter(
                "/QySalesInvoiceHeader",
                "ExternalDocumentNo",
                "eq",
                disposalNo,
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
            return redirect("DisposalDetails", pk=disposalNo)


class DisposalPharmacy(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            userCode = request.session["UserID"]

            response = self.make_soap_request("FnSubmitDisposal", pk, userCode)

            if response == True:
                return JsonResponse({"response": str(response)}, safe=False)
            return JsonResponse({"error": str(response)}, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class DisposalCert(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Pharmacy_Cert_" + pk + ".pdf"
            response = self.make_soap_request("PrintDisposalRequestCertificate", pk)
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
            return redirect("DisposalDetails", pk=pk)


class TechnicalRequirements(UserObjectMixins, View):
    async def get(self, request, pk):
        try:
            required_files = []
            attached = []
            filter = request.GET.get("filter")
            firstTimeApplication = request.GET.get("firstTimeApplication")

            async with aiohttp.ClientSession() as session:
                task = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyInspectorateRequiredDocument",
                        "Class",
                        "eq",
                        filter,
                    )
                )
                task2 = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYDocumentAttachments")
                )
                response = await asyncio.gather(task, task2)

                if firstTimeApplication == "YES":
                    required_files = [
                        x
                        for x in response[0]
                        if x["Category"] == "First time applicant"
                    ]
                elif firstTimeApplication == "NO":
                    required_files = [
                        x for x in response[0] if x["Category"] == "Existing applicant"
                    ]
                else:
                    required_files = [x for x in response[0]]
                attached = [x for x in response[1] if x["No_"] == pk]

                for d in required_files:
                    d["Description"] = d["Description"].replace(" ", "_")
                required_files = [
                    d
                    for d in required_files
                    if not any(a["File_Name"] == d["Description"] for a in attached)
                ]
                return JsonResponse(required_files, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, safe=False)
