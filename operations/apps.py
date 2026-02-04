from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'operations'


    def ready(self) -> None:
        from .signals import register_operations_signals

        register_operations_signals()
