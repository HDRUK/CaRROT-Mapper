import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "mapping",
    "shared",
    "shared.files",
]

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("COCONNECT_DB_ENGINE"),
        "HOST": os.environ.get("COCONNECT_DB_HOST"),
        "PORT": os.environ.get("COCONNECT_DB_PORT"),
        "NAME": os.environ.get("COCONNECT_DB_NAME"),
        "USER": os.environ.get("COCONNECT_DB_USER"),
        "PASSWORD": os.environ.get("COCONNECT_DB_PASSWORD"),
        "TEST": {
            "NAME": "throwawaydb",
        },
    }
}
