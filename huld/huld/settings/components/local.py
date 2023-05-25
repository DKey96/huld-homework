import os

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "NAME": "huld",
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "localhost",
        "USER": "huld",
        "PASSWORD": "huld",
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "OPTIONS": {"application_name": os.getenv("HOSTNAME", "unknown")},
    },
}
