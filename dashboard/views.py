from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from myRequest.views import UserObjectMixins
import logging

# Create your views here.
class Dashboard(UserObjectMixins,View):
    template_name = 'dashboard.html'
    logger = logging.getLogger('dashboard')
    
    def get(self, request):
        ctx = {}
        try:
            ctx = {

            }
        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("dashboard")
        return render(request, self.template_name, ctx)

