"""
Django settings for HinghwaDict project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
import logging
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import time
import environ

env = environ.Env()
environ.Env.read_env(".env")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY", "DEFAULT_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "article",
    "user",
    "word",
    "music",
    "quiz",
    "website",
    "django_apscheduler",
    "corsheaders",
    "notifications",
    "rewards",

    # 'rest_framework'
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
    "utils.exception.ExceptionMiddleware.ExceptionMiddleware",
]

ROOT_URLCONF = "HinghwaDict.urls"

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

WSGI_APPLICATION = "HinghwaDict.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = "/static/"
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),
# ]
STATIC_ROOT = os.path.join(BASE_DIR, "/static/")

LOGIN_REDIRECT_URL = "/home/"
LOGIN_URL = "/login"
EMAIL_HOST = env.str("EMAIL_HOST", "DEFAULT_EMAIL_HOST")
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "DEFAULT_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "DEFAULT_EMAIL_HOST_PASSWORD")
EMAIL_PORT = env.str("EMAIL_PORT", "DEFAULT_EMAIL_PORT")
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", "DEFAULT_DEFAULT_FROM_EMAIL")
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 媒体图片下载到media/下
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# 跨域访问设置
CORS_ORIGIN_ALLOW_ALL = True

APPEND_SLASH = False

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = (
    "http://127.0.0.1:*",
    "https://api.pxm.edialect.top:*",
    "https://pxm.edialect.top:*",
    "https://localhost:*",
)
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
    "VIEW",
)
CORS_ALLOW_HEADERS = (
    "XMLHttpRequest",
    "X_FILENAME",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "Pragma",
    "x-token",
    "token",
)
# parameter of Tencent cos
COS_SECRET_ID = env.str("COS_SECRET_ID", "DEFAULT_COS_SECRET_ID")  # 替换为用户的 secretId
COS_SECRET_KEY = env.str("COS_SECRET_KEY", "DEFAULT_COS_SECRET_KEY")  # 替换为用户的 secretKey
COS_BUCKET = env.str("COS_BUCKET", "DEFAULT_COS_BUCKET")  # BucketName-APPID
COS_REGION = env.str("COS_REGION", "DEFAULT_COS_REGION")

# parameter of wechat login
APP_ID = env.str("APP_ID", "DEFAULT_APP_ID")
APP_SECRECT = env.str("APP_SECRECT", "DEFAULT_APP_SECRECT")

# parameter of jwt
JWT_KEY = env.str("JWT_KEY", "DEFAULT_JWT_KEY")

import os

log_path = os.path.join(BASE_DIR, "logs")
if not os.path.exists(log_path):
    os.mkdir(log_path)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] [%(levelname)s] : "
            "[%(filename)s:%(lineno)d] [%(module)s:%(funcName)s] "
            "- %(message)s"
        },
        "simple": {"format": "%(levelname)s %(module)s %(lineno)d %(message)s"},
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s"
        },
    },
    "filters": {"require_debug_true": {"()": "django.utils.log.RequireDebugTrue"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "filters": ["require_debug_true"],
        },
        # 默认记录所有日志
        "default": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(
                log_path, "all-{}.log".format(time.strftime("%Y-%m-%d"))
            ),
            "maxBytes": 1024 * 1024 * 5,  # 文件大小
            "backupCount": 5,  # 备份数
            "formatter": "standard",  # 输出格式
            "encoding": "utf-8",  # 设置默认编码，否则打印出来汉字乱码
        },
        # 输出错误日志
        "error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(
                log_path, "error-{}.log".format(time.strftime("%Y-%m-%d"))
            ),
            "maxBytes": 1024 * 1024 * 5,  # 文件大小
            "backupCount": 5,  # 备份数
            "formatter": "standard",  # 输出格式
            "encoding": "utf-8",  # 设置默认编码
        },
        # 输出info日志
        "info": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(
                log_path, "info-{}.log".format(time.strftime("%Y-%m-%d"))
            ),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "standard",
            "encoding": "utf-8",  # 设置默认编码
        },
    },
    # 配置日志处理器
    "loggers": {
        "django": {
            "handlers": ["default", "console"],
            "level": "INFO",  # 日志器接收的最低日志级别
            "propagate": True,
        },
        # log 调用时需要当作参数传入
        "log": {
            "handlers": ["error", "info", "console", "default"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAdminUser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 15,
}

# 保存的拼音语料.mp3
# 分为submit和combine两个文件夹
SAVED_PINYIN = os.path.join(BASE_DIR, "material", "audio")
TIME_ZONE = "Asia/Shanghai"
USE_TZ = True
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "default_cache_table",
    },
    "pronunciation_ranking": {
        "TIMEOUT": 900,
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "pronunciation_ranking_cache_table",
    },
}
