from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver


User = get_user_model()

class AccountType(models.Model):
    account_name = models.CharField(max_length=255)
    min_amount = models.FloatField()
    max_amount = models.FloatField()
    is_public = models.BooleanField(default=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_account_types', default=1)

    def __str__(self):
        return self.account_name
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
      

    def __str__(self):
        return f"{self.user.username} saved {self.amount} to {self.account_type.account_name}"

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username}'s {self.account_type.account_name} Account"

    def update_balance(self):
        transactions = Transaction.objects.filter(user=self.user, account_type=self.account_type)
        total_balance = sum(transaction.amount for transaction in transactions)
        self.balance = total_balance

    def save(self, *args, **kwargs):
        # Disconnect the signal temporarily to avoid recursion
        post_save.disconnect(receiver=update_balance, sender=Account)

        self.update_balance()
        super().save(*args, **kwargs)

        # Reconnect the signal after saving
        post_save.connect(receiver=update_balance, sender=Account)

    def has_paid_registration(self):
        registration_account = AccountType.objects.get(account_name='Registration Account')
        registration_balance = Account.objects.filter(user=self.user, account_type=registration_account).first()

        if registration_balance:
            return registration_balance.balance >= 500
        else:
            return False

@receiver(post_save, sender=Account)
def update_balance(sender, instance, **kwargs):
    instance.update_balance()
    instance.save()