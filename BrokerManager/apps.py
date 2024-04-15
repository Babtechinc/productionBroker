from django.apps import AppConfig


class BrokermanagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BrokerManager'

    def ready(self):
        from . import signals  # Import and register signals

        from .mqtt_consumer import client
        # MQTT Consumer : Start Loop
        client.loop_start()