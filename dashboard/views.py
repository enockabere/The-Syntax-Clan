from django.shortcuts import render, redirect
from django.conf import settings as config
from django.contrib import messages
import requests
import json
from datetime import date


def get_object(endpoint):
    session = requests.Session()
    session.auth = config.AUTHS
    response = session.get(endpoint, timeout=10).json()
    return response


# Create your views here.
def dashboard(request):
    q = request.GET.get("q")
    all = []
    try:
        userId = request.session["UserID"]
        LTR_Email = request.session["LTR_Email"]
        LTR_Name = request.session["LTR_Name"]
        Country = request.session["Country"]
        Business_Registration_No_ = request.session["Business_Registration_No_"]
        if q is None or q == "Wholesale":
            Access_Point = config.O_DATA.format(
                f"/QyWholesalePremisePermit?$filter=UserCode%20eq%20%27{userId}%27"
            )
        elif q == "Retail":
            Access_Point = config.O_DATA.format(
                f"/QyRetailDealersPremisePermit?$filter=UserCode%20eq%20%27{userId}%27"
            )
        elif q == "Advertisement":
            Access_Point = config.O_DATA.format(
                f"/QyAdvertisement?$filter=UserCode%20eq%20%27{userId}%27"
            )
        elif q == "Disposal":
            Access_Point = config.O_DATA.format(
                f"/QyDisposalRequest?$filter=UserCode%20eq%20%27{userId}%27"
            )
        elif q == "Manufacturing":
            Access_Point = config.O_DATA.format(
                f"/QyManufacturingLicence?$filter=UserCode%20eq%20%27{userId}%27"
            )
        response = get_object(Access_Point)

        OpenProducts = [x for x in response["value"] if x["Status"] == "Open"]
        Pending = [x for x in response["value"] if x["Status"] == "Processing"]
        Approved = [x for x in response["value"] if x["Status"] == "Approved"]
        Rejected = [x for x in response["value"] if x["Status"] == "Rejected"]

        all = response["value"]

    except requests.exceptions.RequestException as e:
        messages.error(request, e)
        print(e)
        return redirect("dashboard")
    except KeyError as e:
        messages.info(request, "Session Expired, Login Again")
        print(e)
        return redirect("login")
    openCount = len(OpenProducts)
    pendCount = len(Pending)
    appCount = len(Approved)
    rejectedCount = len(Rejected)
    ctx = {
        "openCount": openCount,
        "open": OpenProducts,
        "pendCount": pendCount,
        "pending": Pending,
        "appCount": appCount,
        "approved": Approved,
        "rejectedCount": rejectedCount,
        "rejected": Rejected,
        "all": all,
        "userID": userId,
        "LTR_Name": LTR_Name,
        "Country": Country,
        "LTR_Email": LTR_Email,
        "Business_Registration_No_": Business_Registration_No_,
        "q": q,
    }
    return render(request, "dashboard.html", ctx)
