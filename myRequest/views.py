from django.conf import settings as config
import datetime as dt
import secrets
import string
from django.template.loader import render_to_string
import datetime as dt
from django.core.mail import EmailMessage
import threading

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

class UserObjectMixins(object):
    todays_date = dt.datetime.now().strftime("%b. %d, %Y %A")

    def verificationToken(self, tokenRange):
        digits = string.digits
        secret_code = "".join(secrets.choice(digits) for _ in range(tokenRange))
        return secret_code
    
    def send_mail(self, subject, template, recipient, recipient_email, verification_link):
        email_body = render_to_string(template, {
            "user": recipient,
            "verification_link": verification_link,
        })
        email = EmailMessage(
            subject=subject,
            body=email_body,
            from_email=config.EMAIL_HOST_USER,
            to=[recipient_email]
        )
        email.content_subtype = "html"
        EmailThread(email).start()
        return True


