from pathlib import Path
import os
from decouple import config, Csv
from requests import Session
from zeep import Client
from requests.auth import HTTPBasicAuth
from zeep.transports import Transport
import logging


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGGING_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "django.log"),
        },
         "authentication_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGGING_DIR, "authentication.log"),
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
        "authentication": {
            "handlers": ["authentication_file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


MODE = config("MODE", default="dev")
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = [".localhost", ".127.0.0.1"]

AUTH_USER_MODEL = "authentication.CustomUser"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "authentication",
    "base",
    "dashboard",
    "registration",
    "pharmaceutical",
    "vaccine",
    "pesticide",
    "feed",
    "biocidal",
    "devices",
    "variation",
    "appeal",
    "payment",
    "retention",
    "renewal",
    "gmp",
    "myRequest",
    "permit",
    "retailers",
    "advertisement",
    "disposal",
    "manufacturing",
    'django.contrib.gis',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
CONTENT_SECURITY_POLICY = "default-src 'self'; script-src 'self'; style-src 'self';"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": "",
    }
}

ROOT_URLCONF = "SYNTAX_CLAN.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "SYNTAX_CLAN.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

ENCRYPT_KEY = b"bzKNyzSwwsN0pwQKglGqPnMKPS6WTPElkRPoCOTYN0I="


STATIC_URL = "/selfservice/static/"
MEDIA_URL = "/selfservice/images/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# configuring the location for media
MEDIA_URL = "/selfservice/images/"
MEDIA_ROOT = os.path.join(BASE_DIR, "images")


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PESAFLOW_CLIENT_ID = config("PESAFLOW_CLIENT_ID")
PESAFLOW_CLIENT_SECRET = config("PESAFLOW_CLIENT_SECRET")
SSO_CLIENT_ID = config("SSO_CLIENT_ID")
SSO_CLIENT_SECRET = config("SSO_CLIENT_SECRET")
REDIRECT_URI = config("REDIRECT_URI")
AUTH_URL = config("AUTH_URL")
TOKEN_URL = config("TOKEN_URL")
USER_INFO_URL = config("USER_INFO_URL")
SERVICE_ID = config("SERVICE_ID")
NOTIFICATION_URL = config("NOTIFICATION_URL")
KEY = config("KEY")
API_URL = config("API_URL")


AUTHS = Session()

WEB_SERVICE_PWD = "Password@312"
WEB_SERVICE_UID = "KTL-ADMIN"

BASE_URL = "http://20.120.96.92:2047/BC200/WS/VMD%20TEST%20LIVE/Codeunit/WebPortal"
O_DATA = "http://20.120.96.92:2048/BC200/ODataV4/Company(%27VMD%20TEST%20LIVE%27){}"
AUTHS.auth = HTTPBasicAuth("KTL-ADMIN", WEB_SERVICE_PWD)

CLIENT = Client(BASE_URL, transport=Transport(session=AUTHS))
AUTHS = HTTPBasicAuth("KTL-ADMIN", WEB_SERVICE_PWD)