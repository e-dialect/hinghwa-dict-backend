from django.apps import AppConfig


class WordConfig(AppConfig):
    name = "word"
    verbose_name_plural = "词语模块管理"
    verbose_name = "词语模块管理"

    def ready(self):
        from .search import signals  # noqa: F401
