from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from myRequest.views import UserObjectMixins
import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from authentication.models import CustomUser
from savings.models import Transaction,AccountType
from django.db.models import Case, When, Sum, F, DecimalField


# Create your views here.
class Dashboard(UserObjectMixins, View):
    template_name = 'dashboard.html'
    logger = logging.getLogger('admin_dashboard')

    @method_decorator(login_required(login_url='Login')) 
    def get(self, request):
        ctx = {}
        try:
            user_data = request.session["user_data"]

            total_users_count = CustomUser.objects.count()
            admin_users_count = CustomUser.objects.filter(is_admin=True).count()
            non_admin_users_count = total_users_count - admin_users_count
            active_users_count = CustomUser.objects.filter(is_active=True).count()
            staff_users_count = CustomUser.objects.filter(is_staff=True).count()
            superusers_count = CustomUser.objects.filter(is_superuser=True).count()
            verified_users_count = CustomUser.objects.filter(is_email_verified=True).count()
            total_accounts = AccountType.objects.count()
            account_types = AccountType.objects.all()
            account_totals = []
            for account_type in account_types:
                total_amount = Transaction.objects.filter(account_type=account_type).aggregate(Sum('amount'))['amount__sum']
                num_customers = Transaction.objects.filter(account_type=account_type).values('user').distinct().count()
                account_totals.append({
                    'account_type': account_type,
                    'total_amount': total_amount or 0,
                    'num_customers': num_customers,
                })
            total_amount_saved = Transaction.objects.exclude(account_type__account_name='Registration Account').aggregate(Sum('amount'))['amount__sum'] or 0.0
            first_transaction = Transaction.objects.earliest('timestamp')
            last_transaction = Transaction.objects.latest('timestamp')
            
            days_between_transactions = (last_transaction.timestamp - first_transaction.timestamp).days
            
            transactions_within_range = Transaction.objects.filter(
                timestamp__range=(first_transaction.timestamp, last_transaction.timestamp)
            ).count()
            
            users_with_transactions = CustomUser.objects.filter(transaction__isnull=False).exclude(account__account_type__account_name='Registration Account')

            user_savings = users_with_transactions.annotate(total_savings=Sum(Case(When(transaction__account_type__account_name='Registration Account', then=0),
                    default=F('transaction__amount'),
                    output_field=DecimalField()
                )
            )).order_by('-total_savings')
            ctx = {
                'total_users_count': total_users_count,
                'admin_users_count': admin_users_count,
                'non_admin_users_count': non_admin_users_count,
                'active_users_count': active_users_count,
                'staff_users_count': staff_users_count,
                'superusers_count': superusers_count,
                'verified_users_count': verified_users_count,
                'user_data': user_data,
                'total_accounts': total_accounts,
                'account_totals': account_totals,
                'total_amount_saved': total_amount_saved,
                'days_between_transactions': days_between_transactions,
                'transactions_within_range': transactions_within_range,
                'user_savings': user_savings,
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