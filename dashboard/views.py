from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from myRequest.views import UserObjectMixins
import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


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

class UserDashboard(UserObjectMixins, View):
    template_name = 'user_dashboard.html'
    logger = logging.getLogger('user_dashboard')
    
    @method_decorator(login_required(login_url='Login')) 
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        return render(request, self.template_name)