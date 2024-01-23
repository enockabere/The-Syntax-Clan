from django.shortcuts import render,redirect
from django.conf import settings as config
from django.contrib import messages
import requests

# Create your views here.
def biocidalRegistration(request,pk):
    if request.method == 'POST':
        try:
            prodNo = pk
            myAction = 'modify'
            prodName = request.POST.get('prodName')
            otherNames = request.POST.get('otherNames')
            chemicalName = request.POST.get('chemicalName')
            casNumber = request.POST.get('casNumber')
            proposedShelfLife =request.POST.get('proposedShelfLife')
            shelfLifeAfterFirstOpening =request.POST.get('shelfLifeAfterFirstOpening')
            ShelfLifeAfterDilution = request.POST.get('ShelfLifeAfterDilution')
            visualDescription = request.POST.get('visualDescription')
            packagingMaterial = request.POST.get('packagingMaterial')
            closureSystem = request.POST.get('closureSystem')
            packSize = request.POST.get('packSize')
            iAgree = eval(request.POST.get('iAgree'))
            signatoryName = request.POST.get('signatoryName')
            signatoryPosition = request.POST.get('signatoryPosition')
            userId = request.session['UserID']
            companyName = request.POST.get('companyName')
            companyAddress = request.POST.get('companyAddress')
            CountryOrigin = request.POST.get('CountryOrigin')
            companyTel = request.POST.get('companyTel')
            companyFax = request.POST.get('companyFax')
            companyEmail = request.POST.get('companyEmail')

            if not iAgree:
                iAgree = False         
            
            try:
                response = config.CLIENT.service.BiocidalCard(prodNo,myAction,prodName,otherNames,
                chemicalName,casNumber,proposedShelfLife,
                shelfLifeAfterFirstOpening,ShelfLifeAfterDilution,visualDescription,packagingMaterial,
                packSize,closureSystem,userId,iAgree,signatoryName,signatoryPosition,companyName,companyAddress,
                CountryOrigin,companyTel,companyFax,companyEmail)
                print(response)
                if response == True:
                    messages.success(request,"Successfully Saved")
                    return redirect('productDetails', pk=pk)
                else:
                    messages.success(request,"Not sent. Retry Again")
                    return redirect('applications', pk=pk)
            except requests.exceptions.RequestException as e:
                print(e)
                return redirect('applications', pk=pk)
        except KeyError as e:
            messages.info(request,"Session Expired, Login Again")
            print(e)
            return redirect('login')
        except ValueError as e:
            messages.info(request,"Invalid Input")
            print(e)
            return redirect('applications', pk=pk)
    return redirect('applications', pk=pk)