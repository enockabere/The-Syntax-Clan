import asyncio
import logging
import aiohttp
from django.shortcuts import render
import requests
from django.conf import settings as config
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
import base64
import io as BytesIO
from django.http import HttpResponse, JsonResponse
from myRequest.views import UserObjectMixins


class registrationRetention(UserObjectMixins, View):
    async def get(self, request):
        try:
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")
            UserID = await sync_to_async(request.session.__getitem__)("UserID")

            ctx = {}

            async with aiohttp.ClientSession() as session:
                task1 = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QyYears")
                )
                task2 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYRegistration", "User_code", "eq", UserID
                    )
                )
                task3 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYVariation", "User_code", "eq", UserID
                    )
                )
                response = await asyncio.gather(task1, task2, task3)
                years = [x for x in response[0]]
                product = [
                    x
                    for x in response[1]
                    if x["Status"] == "Approved" and x["Selected"] == False
                ]
                ApprovedVariation = [
                    x for x in response[2] if x["Status"] == "Approved"
                ]

                ctx = {
                    "LTR_Name": LTR_Name,
                    "LTR_Email": LTR_Email,
                    "years": years,
                    "product": product,
                    "ApprovedVariation": ApprovedVariation,
                }
        except Exception as e:
            messages.error(request, f"{e}")
            logging.exception(e)
            return redirect("dashboard")
        return render(request, "retention.html", ctx)

    async def post(self, request):
        try:
            retNo = request.POST.get("retNo")
            myAction = request.POST.get("myAction")
            prodNo = request.POST.get("prodNo")
            userId = await sync_to_async(request.session.__getitem__)("UserID")
            VariationNumber = request.POST.get("VariationNumber")
            changesToTheProduct = eval(request.POST.get("changesToTheProduct"))
            variations = request.POST.get("variation")
            yearOfRetention = int(request.POST.get("yearOfRetention"))
            iAgree = eval(request.POST.get("iAgree"))
            signatoryName = request.POST.get("signatoryName")
            signatoryPosition = request.POST.get("signatoryPosition")
            Bulk = False

            if not iAgree:
                iAgree = False

            if not VariationNumber or VariationNumber == "":
                VariationNumber = ""

            if not variations:
                variations = "False"
            if not VariationNumber:
                VariationNumber = ""

            variation = eval(variations)

            response = self.make_soap_request(
                "Retension",
                retNo,
                myAction,
                userId,
                prodNo,
                VariationNumber,
                changesToTheProduct,
                variation,
                iAgree,
                signatoryName,
                signatoryPosition,
                yearOfRetention,
                Bulk,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != "0" and response is not None and response != "":
                    messages.success(request, " Success")
                    return redirect("retention")
                else:
                    messages.error(request, f"{response}")
                    return redirect("retention")
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("retention")


class RetentionDetails(UserObjectMixins, View):
    def get(self, request, pk):
        try:
            logger = logging.getLogger("selfservice")

            current_url = request.get_full_path()
            request.session["saved_url"] = current_url

            userID = request.session["UserID"]
            LTR_Name = request.session["LTR_Name"]
            LTR_Email = request.session["LTR_Email"]
            responses = {}
            Status = None
            prod = None
            vet_class = None
            prod_res = None
            vet_class = None
            VertinaryClasses = None
            ctx = {}
            years = []
            Access_Point = config.O_DATA.format(
                f"/QYRetension?$filter=User_code%20eq%20%27{userID}%27%20and%20Retension_No_%20eq%20%27{pk}%27"
            )
            response = self.get_object(Access_Point)

            current_url = request.get_full_path()
            request.session["saved_url"] = current_url

            for res in response["value"]:
                responses = res
                Status = res["Status"]
                prod = res["ProductNo"]

            Product = config.O_DATA.format(
                f"/QYRegistration?$filter=ProductNo%20eq%20%27{prod}%27"
            )
            prod_details = self.get_object(Product)
            for prod_No in prod_details["value"]:
                prod_res = prod_No
                vet_class = prod_res["Veterinary_Classes"]

            VertinaryClass = config.O_DATA.format(
                f"/QYVertinaryclasses?$filter=Class%20eq%20%27{vet_class}%27"
            )
            VertResponse = self.get_object(VertinaryClass)
            for vertinary_class in VertResponse["value"]:
                VertinaryClasses = vertinary_class

            QyYears = config.O_DATA.format("/QyYears")
            YearsResponse = self.get_object(QyYears)
            years = [x for x in YearsResponse["value"]]

            ctx = {
                "res": responses,
                "status": Status,
                "LTR_Name": LTR_Name,
                "LTR_Email": LTR_Email,
                "VertinaryClasses": VertinaryClasses,
                "years": years,
            }

        except Exception as e:
            messages.error(request, f"{e}")
            logger.error(f"Error in Retention Details.get: {str(e)}")
            return redirect("dashboard")
        return render(request, "single-retention-detail.html", ctx)


class retentionGateway(UserObjectMixins, View):
    def get(self, request, pk):
        try:
            userID = request.session["UserID"]
            LTR_Name = request.session["LTR_Name"]
            LTR_Email = request.session["LTR_Email"]
            Access_Point = config.O_DATA.format(
                f"/QYRetension?$filter=User_code%20eq%20%27{userID}%27%20and%20Retension_No_%20eq%20%27{pk}%27"
            )
            response = self.get_object(Access_Point)
            for res in response["value"]:
                responses = res
                Status = res["Status"]
        except requests.exceptions.RequestException as e:
            messages.error(request, e)
            print(e)
            return redirect("retention")
        except KeyError as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("login")
        ctx = {
            "res": responses,
            "status": Status,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
        }
        return render(request, "retentionGateway.html", ctx)

    def post(self, request, pk):
        if request.method == "POST":
            try:
                transactionCode = request.POST.get("transactionCode")
                currency = request.POST.get("currency")

                if not transactionCode:
                    messages.error(request, "Transaction Code can't be empty.")
                    return redirect("retentionGateway", pk=pk)
                if not currency:
                    messages.error(
                        request, "Currency code missing please contact the system admin"
                    )
                    return redirect("retentionGateway", pk=pk)
                response = config.CLIENT.service.FnConfirmPayment(
                    transactionCode, currency, pk, request.session["UserID"]
                )
                if response == True:
                    messages.success(
                        request,
                        "Payment was successful. You can now submit your application.",
                    )
                    return redirect("retentionDetails", pk=pk)
                else:
                    messages.error(request, "Payment Not sent. Try Again.")
                    return redirect("retentionGateway", pk=pk)
            except requests.exceptions.RequestException as e:
                messages.error(request, e)
                print(e)
                return redirect("retentionGateway", pk=pk)
            except KeyError as e:
                messages.info(request, "Session Expired, Login Again")
                print(e)
                return redirect("login")
            except Exception as e:
                messages.error(request, e)
                return redirect("retentionGateway", pk=pk)
        return redirect("retentionGateway", pk=pk)


class SubmitRetention(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            userCode = request.session["UserID"]

            response = self.make_soap_request("FnSubmitRetention", pk, userCode)

            if response == True:
                return JsonResponse({"response": str(response)}, safe=False)
            return JsonResponse({"error": str(response)}, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class makeRetentionPayment(UserObjectMixins, View):
    async def post(self, request):
        try:
            retentionNo = request.POST.get("retentionNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")

            response = self.make_soap_request(
                "FnRetetionPayment",
                retentionNo,
                userCode,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, " Success")
                    return redirect("retentionDetails", pk=retentionNo)
                else:
                    messages.error(request, f"{response}")
                    return redirect("retentionDetails", pk=retentionNo)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("retentionDetails", pk=retentionNo)


class FNGenerateRetentionInvoice(UserObjectMixins, View):
    def post(self, request):
        try:
            retentionNo = request.POST.get("retentionNo")
            filenameFromApp = "invoice_" + retentionNo + ".pdf"

            response = self.make_soap_request("FnGenerateSalesInvoice", retentionNo)

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
            return redirect("retentionDetails", pk=retentionNo)


class PrintRentetionCertificate(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Retention_Cert_" + pk + ".pdf"
            response = self.make_soap_request("PrintRentetionCertificate", pk)

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
            return redirect("retentionDetails", pk=pk)


class BulkRetention(UserObjectMixins, View):
    async def get(self, request):
        try:
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            ctx = {}

            async with aiohttp.ClientSession() as session:
                task1 = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QYVertinaryclasses")
                )
                task2 = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QyYears")
                )
                response = await asyncio.gather(task1, task2)

                VertinaryClasses = [x for x in response[0]]
                years = [x for x in response[1]]

                ctx = {
                    "LTR_Name": LTR_Name,
                    "LTR_Email": LTR_Email,
                    "VertinaryClasses": VertinaryClasses,
                    "years": years,
                }
        except Exception as e:
            messages.error(request, f"{e}")
            logging.exception(e)
            return redirect("dashboard")
        return render(request, "bulk_retention.html", ctx)

    async def post(self, request):
        try:
            retNo = request.POST.get("retNo")
            myAction = request.POST.get("myAction")
            userId = await sync_to_async(request.session.__getitem__)("UserID")
            yearOfRetention = int(request.POST.get("yearOfRetention"))
            iAgree = eval(request.POST.get("iAgree"))
            veterinaryClass = request.POST.get("veterinaryClass")
            signatoryName = request.POST.get("signatoryName")
            signatoryPosition = request.POST.get("signatoryPosition")
            Bulk = True

            if not iAgree:
                iAgree = False
            response = self.make_soap_request(
                "FnBulkRetention",
                retNo,
                myAction,
                userId,
                iAgree,
                signatoryName,
                signatoryPosition,
                yearOfRetention,
                veterinaryClass,
                Bulk,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != "0" and response is not None and response != "":
                    messages.success(request, "Success")
                    return redirect("BulkDetails", pk=response)
                else:
                    messages.error(request, f"{response}")
                    return redirect("BulkRetention")
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("BulkRetention")


class BulkDetails(UserObjectMixins, View):
    async def get(self, request, pk):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")
            user_data = await sync_to_async(request.session.__getitem__)("user_data")
            res = {}
            Veterinary_Class = None
            lines = []

            current_url = request.get_full_path()
            request.session["saved_url"] = current_url

            async with aiohttp.ClientSession() as session:
                task1 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QYRetension",
                        "Retension_No_",
                        "eq",
                        pk,
                    )
                )
                task2 = asyncio.ensure_future(
                    self.simple_fetch_data(session, "/QyYears")
                )
                task3 = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session,
                        "/QyRetentionLines",
                        "RetensionNo",
                        "eq",
                        pk,
                    )
                )
                response = await asyncio.gather(task1, task2, task3)
                for retention in response[0]:
                    if retention["User_code"] == userID:
                        res = retention
                        Veterinary_Class = retention["Veterinary_Classes"]
                years = [x for x in response[1]]
                Product_url = config.O_DATA.format(
                    f"/QYRegistration?$filter=User_code%20eq%20%27{userID}%27%20and%20Status%20eq%20%27Approved%27"
                )
                prod_response = self.get_object(Product_url)
                products = [
                    x
                    for x in prod_response["value"]
                    if x["Selected"] == False
                    and x["Veterinary_Classes"] == Veterinary_Class
                    and x["Retained"] == False
                ]
                lines = [x for x in response[2]]
        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        ctx = {
            "res": res,
            "years": years,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "products": products,
            "lines": lines,
            "user_data": user_data,
        }
        return render(request, "bulk_details.html", ctx)

    async def post(self, request, pk):
        try:
            myAction = request.POST.get("myAction")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")
            prodNo = request.POST.get("prodNo")
            response = self.make_soap_request(
                "FnBulkRetentionLines", pk, myAction, userCode, prodNo
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response == True:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response == True:
                    messages.success(request, " Success")
                    return redirect("BulkDetails", pk=pk)
                else:
                    messages.error(request, f"{response}")
                    return redirect("BulkDetails", pk=pk)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("BulkDetails", pk=pk)


class MyRetentions(UserObjectMixins, View):
    async def get(self, request):
        try:
            userID = await sync_to_async(request.session.__getitem__)("UserID")
            LTR_Name = await sync_to_async(request.session.__getitem__)("LTR_Name")
            LTR_Email = await sync_to_async(request.session.__getitem__)("LTR_Email")

            async with aiohttp.ClientSession() as session:
                task_get_permits = asyncio.ensure_future(
                    self.simple_one_filtered_data(
                        session, "/QYRetension", "User_code", "eq", userID
                    )
                )

                response = await asyncio.gather(task_get_permits)

                new = [
                    x for x in response[0] if x["Application_Stage"] == "Not-Submitted"
                ]
                submitted = [
                    x for x in response[0] if x["Application_Stage"] == "Submitted"
                ]

        except Exception as e:
            messages.info(request, f"{e}")
            print(e)
            return redirect("dashboard")
        ctx = {
            "userID": userID,
            "LTR_Name": LTR_Name,
            "LTR_Email": LTR_Email,
            "new": new,
            "submitted": submitted,
        }
        return render(request, "my_retentions.html", ctx)


class BulkProducts(UserObjectMixins, View):
    def get(self, request, pk):
        try:
            PermitLines = self.one_filter(
                "/QyRetentionLines",
                "RetensionNo",
                "eq",
                pk,
            )

            return JsonResponse(PermitLines, safe=False)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, safe=False)


class bulk_customer(UserObjectMixins, View):
    async def post(self, request):
        try:
            retentionNo = request.POST.get("retentionNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")

            response = self.make_soap_request(
                "FnRetentionBulkInvoice",
                retentionNo,
                userCode,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != None and response != "" and response != 0:
                    messages.success(request, " Success")
                    return redirect("BulkDetails", pk=retentionNo)
                else:
                    messages.error(request, f"{response}")
                    return redirect("BulkDetails", pk=retentionNo)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("BulkDetails", pk=retentionNo)


class BulkInvoice(UserObjectMixins, View):
    def post(self, request):
        try:
            retentionNo = request.POST.get("retentionNo")
            filenameFromApp = "invoice_" + retentionNo + ".pdf"
            invoice_number = None
            invoices = self.one_filter(
                "/QySalesInvoiceHeader",
                "ExternalDocumentNo",
                "eq",
                retentionNo,
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
            return redirect("BulkDetails", pk=retentionNo)


class RetentionCert(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Retention_Cert_" + pk + ".pdf"
            response = self.make_soap_request("PrintRentetionCertificate", pk)
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
            return redirect("BulkDetails", pk=pk)


class RetentionReceipt(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Retention_Receipt_" + pk + ".pdf"
            response = self.make_soap_request("PrintRentetionCertificate", pk)
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
            return redirect("BulkDetails", pk=pk)


class BulkCerts(UserObjectMixins, View):
    def post(self, request, pk):
        try:
            filenameFromApp = "Retention_Cert_" + pk + ".pdf"
            redirect_id = request.POST.get("redirect_id")
            retention_number = None
            retentions = self.one_filter(
                "/QYRetension",
                "ProductNo",
                "eq",
                pk,
            )
            for number in retentions[1]:
                retention_number = number["Retension_No_"]

            response = self.make_soap_request(
                "PrintRentetionCertificate", retention_number
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
            return redirect("BulkDetails", pk=redirect_id)


class normal_customer(UserObjectMixins, View):
    async def post(self, request):
        try:
            retentionNo = request.POST.get("retentionNo")
            userCode = await sync_to_async(request.session.__getitem__)("UserID")

            response = self.make_soap_request(
                "FnRetentionInvoice",
                retentionNo,
                userCode,
            )
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if response != None and response != "" and response != 0:
                    return JsonResponse({"response": str(response)}, safe=False)
                return JsonResponse({"error": str(response)}, safe=False)
            else:
                if response != None and response != "" and response != 0:
                    messages.success(request, " Success")
                    return redirect("retentionDetails", pk=retentionNo)
                else:
                    messages.error(request, f"{response}")
                    return redirect("retentionDetails", pk=retentionNo)
        except Exception as e:
            logging.exception(e)
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"error": str(e)}, safe=False)
            else:
                messages.error(request, f"{e}")
                return redirect("retentionDetails", pk=retentionNo)
