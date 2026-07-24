import logging
from django.apps import AppConfig

logger = logging.getLogger("django_service.api")


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "django_service.api"
    verbose_name = "Semantic Retrieval API"
