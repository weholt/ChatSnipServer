from django.apps import AppConfig


class ChatsnipserverConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatsnipserver"

    def ready(self):
        import chatsnipserver.signals
