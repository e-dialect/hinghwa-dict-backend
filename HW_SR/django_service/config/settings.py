from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 与主项目对齐：使用 environ 统一管理环境变量
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "unsafe-development-key-change-in-production"),
    ALLOWED_HOSTS=(list, ["*"]),
    DB_NAME=(str, str(BASE_DIR / "data" / "db.sqlite3")),
    HW_SR_SERVICE_PORT=(int, 8001),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# 确保 src 等模块可被导入
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_service.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "django_service.config.urls"

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
    }
]

WSGI_APPLICATION = "django_service.config.wsgi.application"
ASGI_APPLICATION = "django_service.config.asgi.application"

# 确保 DB_NAME 总是相对于 BASE_DIR 的绝对路径
_db_name = env("DB_NAME")
if not os.path.isabs(_db_name):
    _db_name = str(BASE_DIR / _db_name)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _db_name,
    }
}

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

APPEND_SLASH = False

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# HW_SR 语义检索服务端口
HW_SR_SERVICE_PORT = env("HW_SR_SERVICE_PORT")

LOG_PATH = BASE_DIR / "logs"
LOG_PATH.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(LOG_PATH / "service.log"),
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django_service": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

logging.getLogger("django_service").info("Django service settings loaded")