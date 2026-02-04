from django.apps import AppConfig


class ActorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'actors'

    def ready(self):
        from actors.signals import register_main_actor_signals

        register_main_actor_signals()
