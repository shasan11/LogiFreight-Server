from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales'

    def ready(self) -> None:
        from .signals import register_sales_signals

        register_sales_signals()
