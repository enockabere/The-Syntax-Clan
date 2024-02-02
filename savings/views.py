from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.views import View
from myRequest.views import UserObjectMixins
import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import AccountType,Transaction, Account


class AccountTypes(UserObjectMixins, View):
    template_name = 'account_type.html'
    logger = logging.getLogger('savings')
    
    @method_decorator(login_required(login_url='Login')) 
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            user_data = request.session["user_data"]
            account_types = AccountType.objects.all()
            ctx = {
                "user_data": user_data,
                "account_types": account_types,
            }
        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("dashboard")
        return render(request, self.template_name, ctx)
    def post(self,request):
        try:
            account_name = request.POST.get('account_name')
            min_amount = float(request.POST.get('min_amount'))
            max_amount = float(request.POST.get('max_amount'))
            is_public = eval(request.POST.get('is_public'))
            
            creator = request.user if request.user.is_authenticated else None
            
            account_type = AccountType(
                account_name=account_name,
                min_amount=min_amount,
                max_amount=max_amount,
                is_public=is_public,
                creator=creator
            )
            account_type.save()
            messages.success(request, 'Account type created successfully.')
            return redirect("admin_account_types")
            
        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("admin_account_types")
        
        
class TransactionsTest(UserObjectMixins, View):
    template_name = 'transactions.html'
    logger = logging.getLogger('savings')
    
    @method_decorator(login_required(login_url='Login')) 
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            user_data = request.session["user_data"]
            transactions = Transaction.objects.all()
            account_types = AccountType.objects.all()
            ctx = {
                "user_data": user_data,
                "transactions": transactions,
                "account_types": account_types,
            }
        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("dashboard")
        return render(request, self.template_name, ctx)
    
    def post(self, request):
        try:
            account_type_id = int(request.POST.get('account_type'))
            amount = float(request.POST.get('amount'))
            
            account_type = get_object_or_404(AccountType, pk=account_type_id)

            user = request.user if request.user.is_authenticated else None
            
            if not Account.objects.filter(user=user, account_type__account_name='Registration Account').exists():
                # Process the payment and save the transaction
                transaction = Transaction(user=user, account_type=account_type, amount=amount)
                transaction.save()

                # Create or update the user's account balance
                account, created = Account.objects.get_or_create(user=user, account_type=account_type)
                account.update_balance()
                account.save()

                messages.success(request, f'Amount of {amount} saved successfully.')
                return redirect("admin_transactions_test")
            else:
                messages.error(request, 'You have already paid the registration fees.')
                return redirect("admin_transactions_test")
            
        except Exception as e:
            messages.info(request, "Session Expired, Login Again")
            print(e)
            return redirect("admin_transactions_test")

