from django.apps import AppConfig


class EditlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "editlog"

    def ready(self):
        from . import file_logger  # noqa: F401
