from django.apps import AppConfig


class PurchaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'purchase'

    def ready(self) -> None:
        from .signals import register_purchase_signals

        register_purchase_signals()
