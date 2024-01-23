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


class RetailersPermit(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task_get_permits = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyRetailDealersPremisePermit",
                        "UserCode",
                        "eq",
                        userID,
                    )
                )
                task_get_countries = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYCountries")
                )
                task_get_inspection = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QyRetailInspection")
                )

                task4 = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QyQualification")
                )

                response = await asyncio.gather(
                    task_get_permits, task_get_countries, task_get_inspection, task4
                )

                permits = [x for x in response[0]]
                Approved = [x for x in response[0] if x["Status"] == "Approved"]
                resCountry = [x for x in response[1]]
                Approved_Inspection = [
                    x for x in response[2] if x["Status"] == "Approved"
                ]
                qualifications = [x for x in response[3]]

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
            "Approved_Inspection": Approved_Inspection,
            "qualifications": qualifications,
        }
        return render(request, "retailer.html", ctx)

    async def post(self, request):
        try:
            retailDealersNo = request.POST.get("retailDealersNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            premiseName = request.POST.get("premiseName")
            town = request.POST.get("town")
            road = request.POST.get("road")
            building = request.POST.get("building")
            applicantName = request.POST.get("applicantName")
            iAgree = eval(request.POST.get("iAgree"))
            myAction = request.POST.get("myAction")
            firstTimeApplication = int(request.POST.get("firstTimeApplication"))
            inspectionNo = request.POST.get("inspectionNo")
            name = request.POST.get("name")
            professionalRegNo = request.POST.get("professionalRegNo")
            email = request.POST.get("email")
            cellPhone = request.POST.get("cellPhone")
            qualification = request.POST.get("qualification")
            plotNo = request.POST.get("plotNo")
            application_year = int(request.POST.get("application_year"))
            alternative_cellPhone = request.POST.get("alternative_cellPhone")

            if not iAgree:
                iAgree = False

            if not inspectionNo and firstTimeApplication == 1:
                inspectionNo = "None"

            if not alternative_cellPhone:
                alternative_cellPhone = ""

            if not inspectionNo and firstTimeApplication == 2:
                if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                    return JsonResponse(
                        {"error": "Previous inspection number missing"}, safe=False
                    )
                else:
                    messages.error(request, "Previous inspection number missing")
                    return redirect("RetailerPermitDetails", pk=retailDealersNo)

            if len(cellPhone) != 10:
                if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                    return JsonResponse(
                        {"error": "Cell Phone number digits must be equal to 10"},
                        safe=False,
                    )
                else:
                    messages.error(
                        request, "Cell Phone number digits must be equal to 10"
                    )
                    return redirect("PermitDetails", pk=retailDealersNo)
            if application_year < 2024:
                if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                    return JsonResponse(
                        {"error": "The application year starts from 2024"},
                        safe=False,
                    )
                else:
                    messages.error(request, "The application year starts from 2024")
                    return redirect("PermitDetails", pk=retailDealersNo)

            response = self.make_soap_request(
                "FnRetailDealersPremisePermit",
                retailDealersNo,
                userCode,
                premiseName,
                building,
                town,
                road,
                building,
                applicantName,
                firstTimeApplication,
                iAgree,
                myAction,
                inspectionNo,
                name,
                professionalRegNo,
                email,
                cellPhone,
                qualification,
                plotNo,
                alternative_cellPhone,
                application_year,
            )

            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != "0" and response is not None and response != "":
                    messages.success(request, "Success")
                    return redirect("RetailerPermitDetails", pk=response)
                else:
                    messages.error(request, f"{response}")
                    return redirect("RetailerPermitDetails", pk=response)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("RetailerPermitDetails", pk=response)


class RetailApplications(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task_get_retail = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyRetailDealersPremisePermit",
                        "UserCode",
                        "eq",
                        userID,
                    )
                )
                response = await asyncio.gather(task_get_retail)
                new_retail = [
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
            "new_retail": new_retail,
            "submitted": submitted,
        }
        return render(request, "retail_apps.html", ctx)


class RetailerPermitDetails(UserObjectMixins, View):
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
                        "/QyRetailDealersPremisePermit",
                        "RetailDealersNo",
                        "eq",
                        pk,
                    )
                )
                task_get_countries = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYCountries")
                )
                task4 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyRetailDealersPremiseLines",
                        "RetailDealersNo",
                        "eq",
                        pk,
                    )
                )
                task5 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYDocumentAttachments", "No_", "eq", pk
                    )
                )
                task6 = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QyQualification")
                )
                response = await asyncio.gather(
                    task_get_permit, task_get_countries, task4, task5, task6
                )
                for permit in response[0]:
                    if permit["UserCode"] == userID:
                        permit = permit
                resCountry = [x for x in response[1]]
                lines = [x for x in response[2]]
                attachments = [x for x in response[3]]
                qualifications = [x for x in response[4]]
        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
            return JsonResponse(permit, safe=False)

        ctx = {
            "permit": permit,
            "country": resCountry,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "lines": lines,
            "attachments": attachments,
            "qualifications": qualifications,
        }
        return render(request, "retailer-detail.html", ctx)

    async def post(self, request, pk):
        try:
            myAction = request.POST.get("myAction")
            lineNo = request.POST.get("lineNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            pro_name = request.POST.get("pro_name")
            position_in_business = request.POST.get("position_in_business")
            Qualification = request.POST.get("Qualification")
            iDorPassportOrAlienIDNo = request.POST.get("iDorPassportOrAlienIDNo")
            nationality = request.POST.get("nationality")
            professionalRegNo = request.POST.get("professionalRegNo")
            Experience = request.POST.get("Experience")

            response = self.make_soap_request(
                "FnRetailDealersLine",
                pk,
                myAction,
                lineNo,
                pro_name,
                position_in_business,
                iDorPassportOrAlienIDNo,
                nationality,
                professionalRegNo,
                Qualification,
                userCode,
                Experience,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, "Success")
                    return redirect("RetailerPermitDetails", pk=pk)
                else:
                    messages.error(request, f"{response}")
                    return redirect("RetailerPermitDetails", pk=pk)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("RetailerPermitDetails", pk=pk)


class RetailProfessionals(UserObjectMixins, View):
    def get(self, request, pk):
        try:
            PermitLines = self.one_filter(
                "/QyRetailDealersPremiseLines",
                "RetailDealersNo",
                "eq",
                pk,
            )

            return JsonResponse(PermitLines, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class RetailCustomer(UserObjectMixins, View):
    async def post(self, request):
        try:
            RetailDealersNo = request.POST.get("RetailDealersNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")

            response = self.make_soap_request(
                "FnRetailDealersPremisePermitPayment",
                RetailDealersNo,
                userCode,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, "Success")
                    return redirect("RetailerPermitDetails", pk=RetailDealersNo)
                else:
                    messages.error(request, f"{response}")
                    return redirect("RetailerPermitDetails", pk=RetailDealersNo)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("RetailerPermitDetails", pk=RetailDealersNo)


class RetailPermitAttachments(UserObjectMixins, View):
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
            tableID = 50050
            fileName = request.POST.get("attachmentCode")
            response = False

            _, file_extension = os.path.splitext(attachment.name)
            fileName_with_extension = f"{fileName}{file_extension}"
            attachment_data = base64.b64encode(attachment.read())

            response = self.make_soap_request(
                "FnAttachementRetailDealersPremisePermit",
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


class RemoveRetailAttachment(UserObjectMixins, View):
    def post(self, request):
        try:
            docID = int(request.POST.get("docID"))
            tableID = int(request.POST.get("tableID"))
            leaveCode = request.POST.get("leaveCode")

            response = self.make_soap_request(
                "FnDeleteDocumentAttachment", leaveCode, docID, tableID
            )
            if response == True:
                return JsonResponse(
                    {"success": True, "message": "Deleted successfully"}
                )
            return JsonResponse({"success": False, "message": f"{response}"})
        except Exception as e:
            error = "Upload failed: {}".format(e)
            logging.exception(e)
            return JsonResponse({"success": False, "error": error})


class RetailerInvoice(UserObjectMixins, View):
    def post(self, request):
        try:
            premiseNo = request.POST.get("premiseNo")
            filenameFromApp = "invoice_" + premiseNo + ".pdf"

            invoice_number = None
            invoices = self.one_filter(
                "/QySalesInvoiceHeader",
                "ExternalDocumentNo",
                "eq",
                premiseNo,
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
            return redirect("RetailerPermitDetails", pk=premiseNo)


class SubmitRetailPermit(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            userCode = request.session["UserID"]

            response = self.make_soap_request("FnSubmitRetailPermit", pk, userCode)

            if response == True:
                return JsonResponse({"response": str(response)}, safe=False)
            return JsonResponse({"error": str(response)}, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class RetailPremiseCert(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Premise_Cert_" + pk + ".pdf"
            response = self.make_soap_request(
                "PrintRetailDealersPremisePermitCertificate", pk
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
            return redirect("RetailerPermitDetails", pk=pk)


class PrintRetailDealersPermitApplicationForm(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "RetailDealersPermitApplicationForm" + pk + ".pdf"

            response = self.make_soap_request(
                "PrintRetailDealersPermitApplicationForm", pk
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
            messages.error(request, e)
            print(e)
            return redirect("RetailerPermitDetails", pk=pk)
